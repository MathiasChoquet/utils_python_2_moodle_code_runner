"""
Module pour analyser les fichiers de tests unittest.
Extrait les classes de test et leurs méthodes pour générer les test cases Moodle.
"""

import ast
import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TestMethod:
    """Information sur une méthode de test."""
    name: str
    docstring: Optional[str]
    source_code: str
    lineno: int
    is_first: bool = False  # Premier test = exemple


@dataclass
class TestClass:
    """Information sur une classe de test unittest."""
    name: str
    docstring: Optional[str]
    tested_function: str  # Nom de la fonction testée (extrait du nom de la classe)
    methods: List[TestMethod]
    setup_code: Optional[str] = None  # Code de la méthode setUp si présente


class UnittestAnalyzer:
    """Analyseur de fichiers unittest."""

    def __init__(self, source_code: str):
        """
        Initialise l'analyseur avec le code source.

        Args:
            source_code: Code source du fichier unittest
        """
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Erreur de syntaxe lors du parsing du fichier unittest: {e}")
            raise

    def analyze(self) -> Dict[str, TestClass]:
        """
        Analyse le fichier unittest et extrait toutes les classes de test.

        Returns:
            Dictionnaire {nom_fonction_testée: TestClass}
        """
        test_classes = {}

        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                # Vérifier si c'est une classe de test (hérite de unittest.TestCase)
                if self._is_test_class(node):
                    test_class = self._extract_test_class(node)
                    if test_class:
                        test_classes[test_class.tested_function] = test_class
                        logger.debug(
                            f"Classe de test trouvée: {test_class.name} "
                            f"pour la fonction {test_class.tested_function}"
                        )

        logger.info(f"Fichier unittest analysé: {len(test_classes)} classes de test")
        return test_classes

    def _is_test_class(self, node: ast.ClassDef) -> bool:
        """
        Vérifie si une classe est une classe de test unittest.

        Args:
            node: Nœud AST de la classe

        Returns:
            True si c'est une classe de test
        """
        for base in node.bases:
            # Vérifie si hérite de unittest.TestCase ou TestCase
            if isinstance(base, ast.Attribute):
                if base.attr == 'TestCase':
                    return True
            elif isinstance(base, ast.Name):
                if base.id == 'TestCase':
                    return True
        return False

    def _extract_test_class(self, node: ast.ClassDef) -> Optional[TestClass]:
        """
        Extrait les informations d'une classe de test.

        Args:
            node: Nœud AST de la classe

        Returns:
            TestClass ou None si le format est invalide
        """
        class_name = node.name

        # Extraire le nom de la fonction testée depuis le nom de la classe
        # Format attendu: Test{NomFonction} ou Test_{NomFonction}
        tested_function = self._extract_tested_function_name(class_name)

        if not tested_function:
            logger.warning(
                f"Impossible d'extraire le nom de la fonction testée "
                f"depuis la classe {class_name}"
            )
            return None

        docstring = ast.get_docstring(node)
        methods = []
        setup_code = None

        # Extraire toutes les méthodes de test
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == 'setUp':
                    setup_code = self._get_source_code(item)
                elif item.name.startswith('test_'):
                    method = self._extract_test_method(item)
                    methods.append(method)

        # Marquer le premier test comme exemple
        if methods:
            methods[0].is_first = True

        logger.debug(f"Classe {class_name}: {len(methods)} méthodes de test")

        return TestClass(
            name=class_name,
            docstring=docstring,
            tested_function=tested_function,
            methods=methods,
            setup_code=setup_code
        )

    def _extract_tested_function_name(self, class_name: str) -> Optional[str]:
        """
        Extrait le nom de la fonction testée depuis le nom de la classe.

        Args:
            class_name: Nom de la classe de test (ex: TestFeetToMeter)

        Returns:
            Nom de la fonction (ex: feet_to_meter) ou None
        """
        # Enlever le préfixe "Test" ou "Test_"
        if class_name.startswith('Test'):
            function_part = class_name[4:]  # Enlever "Test"
            if function_part.startswith('_'):
                function_part = function_part[1:]  # Enlever le "_" si présent

            # Convertir CamelCase en snake_case
            # TestFeetToMeter -> feet_to_meter
            function_name = self._camel_to_snake(function_part)
            return function_name

        return None

    def _camel_to_snake(self, name: str) -> str:
        """
        Convertit CamelCase en snake_case.

        Args:
            name: Nom en CamelCase

        Returns:
            Nom en snake_case
        """
        # Insérer un underscore avant chaque majuscule précédée d'une minuscule
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insérer un underscore avant chaque majuscule précédée d'une lettre ou chiffre
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _extract_test_method(self, node: ast.FunctionDef) -> TestMethod:
        """
        Extrait les informations d'une méthode de test.

        Args:
            node: Nœud AST de la méthode

        Returns:
            TestMethod
        """
        docstring = ast.get_docstring(node)
        source = self._get_source_code(node)

        return TestMethod(
            name=node.name,
            docstring=docstring,
            source_code=source,
            lineno=node.lineno
        )

    def _get_source_code(self, node: ast.AST) -> str:
        """
        Extrait le code source d'un nœud AST.

        Args:
            node: Nœud AST

        Returns:
            Code source du nœud
        """
        try:
            return ast.get_source_segment(self.source_code, node)
        except AttributeError:
            # Fallback pour Python < 3.8
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
            return '\n'.join(self.source_lines[start_line:end_line])


def analyze_unittest_file(filepath: str) -> Dict[str, TestClass]:
    """
    Analyse un fichier unittest et retourne les classes de test.

    Args:
        filepath: Chemin du fichier unittest

    Returns:
        Dictionnaire {nom_fonction_testée: TestClass}

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        SyntaxError: Si le fichier contient des erreurs de syntaxe
    """
    logger.info(f"Analyse du fichier unittest: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        source_code = f.read()

    analyzer = UnittestAnalyzer(source_code)
    return analyzer.analyze()


def validate_test_coverage(functions: List[str], test_classes: Dict[str, TestClass]) -> bool:
    """
    Valide que toutes les fonctions ont leur classe de test.

    Args:
        functions: Liste des noms de fonctions
        test_classes: Dictionnaire des classes de test

    Returns:
        True si toutes les fonctions sont testées

    Raises:
        ValueError: Si une fonction n'a pas de classe de test
    """
    missing_tests = []

    for func_name in functions:
        if func_name not in test_classes:
            missing_tests.append(func_name)

    if missing_tests:
        error_msg = (
            f"Fonctions sans classe de test: {', '.join(missing_tests)}\n"
            f"Chaque fonction doit avoir une classe Test{{NomFonction}}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Toutes les fonctions ont leur classe de test")
    return True
