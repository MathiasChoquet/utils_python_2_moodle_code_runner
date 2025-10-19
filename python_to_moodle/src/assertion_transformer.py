"""
Module pour transformer les assertions unittest en code de test Moodle.
Transforme self.assertEqual(a, b) en print(a) avec expected=b
"""

import ast
import logging
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MoodleTestCase:
    """Représente un cas de test Moodle."""
    testcode: str
    expected: str
    stdin: str = ""
    extra: str = ""


class AssertionTransformer(ast.NodeTransformer):
    """
    Transforme le code de test unittest en code de test Moodle.

    Transformations principales:
    - self.assertEqual(a, b) -> print(a) avec expected=b
    - self.assertTrue(expr) -> print(expr) avec expected=True
    - self.assertFalse(expr) -> print(expr) avec expected=False
    - self.assertRaises(Exception) -> try/except avec print("OK"/"KO")
    """

    def __init__(self):
        self.setup_code = []  # Code de setUp à inclure
        self.test_statements = []  # Statements du test
        self.expected_values = []  # Valeurs attendues
        self.in_with_raises = False  # Dans un contexte assertRaises

    def transform_test_method(self, method_source: str,
                            setup_code: Optional[str] = None) -> MoodleTestCase:
        """
        Transforme une méthode de test unittest en test case Moodle.

        Args:
            method_source: Code source de la méthode de test
            setup_code: Code de setUp optionnel

        Returns:
            MoodleTestCase avec testcode et expected
        """
        logger.debug("Transformation d'une méthode de test")

        # Parser le code
        try:
            tree = ast.parse(method_source)
        except SyntaxError as e:
            logger.error(f"Erreur de parsing du test: {e}")
            raise

        # Trouver la fonction test
        test_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                test_func = node
                break

        if not test_func:
            raise ValueError("Pas de fonction trouvée dans le code de test")

        # Extraire le corps de la fonction (sans def et docstring)
        body = test_func.body

        # Ignorer le docstring s'il est présent
        if (body and isinstance(body[0], ast.Expr) and
            isinstance(body[0].value, ast.Constant)):
            body = body[1:]

        # Transformer les assertions
        transformed_statements = []
        expected_outputs = []

        for stmt in body:
            code, expected = self._transform_statement(stmt)
            if code:
                transformed_statements.append(code)
                if expected is not None:
                    expected_outputs.append(expected)

        # Construire le code de test final
        testcode_lines = []

        # Ajouter le code de setUp si présent
        if setup_code:
            # Extraire seulement le corps de setUp (pas la définition)
            setup_body = self._extract_setup_body(setup_code)
            if setup_body:
                testcode_lines.extend(setup_body)

        # Ajouter les statements transformés
        testcode_lines.extend(transformed_statements)

        testcode = '\n'.join(testcode_lines)
        expected = '\n'.join(str(e) for e in expected_outputs)

        # Nettoyer les retours chariot Windows (\r) pour n'avoir que \n
        testcode = testcode.replace('\r\n', '\n').replace('\r', '\n')
        expected = expected.replace('\r\n', '\n').replace('\r', '\n')

        return MoodleTestCase(testcode=testcode, expected=expected)

    def _extract_setup_body(self, setup_code: str) -> list:
        """
        Extrait le corps de la méthode setUp (sans def et self).

        Args:
            setup_code: Code source de setUp

        Returns:
            Liste des lignes de code
        """
        try:
            tree = ast.parse(setup_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'setUp':
                    body_lines = []
                    for stmt in node.body:
                        # Ignorer le docstring
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                            continue
                        # Convertir self.x en x
                        line = ast.unparse(stmt)
                        line = line.replace('self.', '')
                        body_lines.append(line)
                    return body_lines
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction de setUp: {e}")
        return []

    def _transform_statement(self, stmt: ast.stmt) -> Tuple[Optional[str], Optional[str]]:
        """
        Transforme un statement unittest en code Moodle.

        Args:
            stmt: Statement AST

        Returns:
            Tuple (code_moodle, valeur_attendue)
        """
        # Expression simple (assignment, call, etc.)
        if isinstance(stmt, ast.Expr):
            return self._transform_expr(stmt.value)

        # Assignment
        elif isinstance(stmt, ast.Assign):
            code = ast.unparse(stmt)
            # Enlever self. des assignments
            code = code.replace('self.', '')
            return (code, None)

        # With statement (pour assertRaises)
        elif isinstance(stmt, ast.With):
            return self._transform_with(stmt)

        # Try/except
        elif isinstance(stmt, ast.Try):
            code = ast.unparse(stmt)
            code = code.replace('self.', '')
            return (code, None)

        # For loop (pour les subTest notamment)
        elif isinstance(stmt, ast.For):
            return self._transform_for(stmt)

        # If statement
        elif isinstance(stmt, ast.If):
            code = ast.unparse(stmt)
            code = code.replace('self.', '')
            return (code, None)

        # Autres statements
        else:
            code = ast.unparse(stmt)
            code = code.replace('self.', '')
            return (code, None)

    def _transform_expr(self, expr: ast.expr) -> Tuple[Optional[str], Optional[str]]:
        """Transforme une expression."""

        # Appel de méthode (assertion)
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Attribute):
                method_name = expr.func.attr

                # assertEqual(a, b) -> print(a), expected=b
                if method_name == 'assertEqual':
                    return self._transform_assert_equal(expr)

                # assertTrue(expr) -> print(expr), expected=True
                elif method_name == 'assertTrue':
                    return self._transform_assert_true(expr)

                # assertFalse(expr) -> print(expr), expected=False
                elif method_name == 'assertFalse':
                    return self._transform_assert_false(expr)

                # assertIn(a, b) -> print(a in b), expected=True
                elif method_name == 'assertIn':
                    return self._transform_assert_in(expr)

                # assertRaises -> géré dans _transform_with

        # Expression simple
        code = ast.unparse(expr)
        code = code.replace('self.', '')
        return (code, None)

    def _transform_assert_equal(self, call: ast.Call) -> Tuple[str, str]:
        """
        Transforme self.assertEqual(a, b) en print(a) avec expected=b.
        """
        if len(call.args) < 2:
            logger.warning("assertEqual avec moins de 2 arguments")
            return (ast.unparse(call), None)

        actual = call.args[0]
        expected = call.args[1]

        # Générer print(actual)
        actual_code = ast.unparse(actual)
        actual_code = actual_code.replace('self.', '')
        testcode = f"print({actual_code})"

        # Extraire la valeur attendue
        expected_value = self._extract_value(expected)

        return (testcode, expected_value)

    def _transform_assert_true(self, call: ast.Call) -> Tuple[str, str]:
        """Transforme self.assertTrue(expr) en print(expr) avec expected=True."""
        if len(call.args) < 1:
            return (ast.unparse(call), None)

        expr = call.args[0]
        expr_code = ast.unparse(expr).replace('self.', '')
        testcode = f"print({expr_code})"

        return (testcode, "True")

    def _transform_assert_false(self, call: ast.Call) -> Tuple[str, str]:
        """Transforme self.assertFalse(expr) en print(expr) avec expected=False."""
        if len(call.args) < 1:
            return (ast.unparse(call), None)

        expr = call.args[0]
        expr_code = ast.unparse(expr).replace('self.', '')
        testcode = f"print({expr_code})"

        return (testcode, "False")

    def _transform_assert_in(self, call: ast.Call) -> Tuple[str, str]:
        """Transforme self.assertIn(a, b) en print(a in b) avec expected=True."""
        if len(call.args) < 2:
            return (ast.unparse(call), None)

        item = call.args[0]
        container = call.args[1]

        item_code = ast.unparse(item).replace('self.', '')
        container_code = ast.unparse(container).replace('self.', '')
        testcode = f"print({item_code} in {container_code})"

        return (testcode, "True")

    def _transform_with(self, with_stmt: ast.With) -> Tuple[Optional[str], Optional[str]]:
        """
        Transforme with self.assertRaises(Exception) en try/except.

        with self.assertRaises(ValueError):
            func()

        devient:

        try:
            func()
            print("KO")
        except ValueError:
            print("OK")
        """
        # Vérifier si c'est un assertRaises
        for item in with_stmt.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Attribute):
                    if item.context_expr.func.attr == 'assertRaises':
                        return self._transform_assert_raises(item.context_expr, with_stmt.body)

        # With statement normal
        code = ast.unparse(with_stmt).replace('self.', '')
        return (code, None)

    def _transform_assert_raises(self, call: ast.Call, body: list) -> Tuple[str, str]:
        """Transforme assertRaises en try/except."""
        if len(call.args) < 1:
            return (ast.unparse(call), None)

        exception_type = ast.unparse(call.args[0])

        # Construire le try/except
        body_code = '\n    '.join(ast.unparse(stmt).replace('self.', '') for stmt in body)

        testcode = f"""try:
    {body_code}
    print("KO")
except {exception_type}:
    print("OK")"""

        return (testcode, "OK")

    def _transform_for(self, for_stmt: ast.For) -> Tuple[Optional[str], Optional[str]]:
        """Transforme une boucle for (notamment pour subTest)."""
        code = ast.unparse(for_stmt).replace('self.', '')
        return (code, None)

    def _extract_value(self, node: ast.expr) -> str:
        """
        Extrait la valeur d'un nœud AST comme string.

        Args:
            node: Nœud AST

        Returns:
            Représentation string de la valeur
        """
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.List):
            values = [self._extract_value(elt) for elt in node.elts]
            return '[' + ', '.join(values) + ']'
        elif isinstance(node, ast.Dict):
            items = []
            for k, v in zip(node.keys, node.values):
                items.append(f"{self._extract_value(k)}: {self._extract_value(v)}")
            return '{' + ', '.join(items) + '}'
        else:
            # Pour les expressions complexes, utiliser unparse
            return ast.unparse(node).replace('self.', '')
