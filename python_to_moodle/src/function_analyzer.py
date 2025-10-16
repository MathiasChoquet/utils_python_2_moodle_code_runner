"""
Module pour analyser les fichiers Python et extraire les fonctions et classes.
Utilise l'AST (Abstract Syntax Tree) pour parser le code source.
"""

import ast
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information sur une fonction extraite du code source."""
    name: str
    docstring: Optional[str]
    source_code: str
    lineno: int
    dependencies: Set[str]  # Noms des fonctions appelées
    is_class: bool = False
    class_name: Optional[str] = None


@dataclass
class ModuleInfo:
    """Information sur un module Python."""
    docstring: Optional[str]
    functions: Dict[str, FunctionInfo]
    classes: Dict[str, FunctionInfo]


class FunctionAnalyzer:
    """Analyseur de fonctions et classes Python via AST."""

    def __init__(self, source_code: str):
        """
        Initialise l'analyseur avec le code source.

        Args:
            source_code: Code source Python à analyser
        """
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Erreur de syntaxe lors du parsing: {e}")
            raise

    def analyze(self) -> ModuleInfo:
        """
        Analyse le module et extrait toutes les informations.

        Returns:
            ModuleInfo contenant le docstring du module et toutes les fonctions/classes
        """
        module_docstring = ast.get_docstring(self.tree)
        functions = {}
        classes = {}

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # Vérifier si la fonction est au niveau module (pas dans une classe)
                if self._is_module_level(node):
                    func_info = self._extract_function_info(node)
                    functions[func_info.name] = func_info
                    logger.debug(f"Fonction trouvée: {func_info.name}")

            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                classes[class_info.name] = class_info
                logger.debug(f"Classe trouvée: {class_info.name}")

        logger.info(f"Module analysé: {len(functions)} fonctions, {len(classes)} classes")
        return ModuleInfo(
            docstring=module_docstring,
            functions=functions,
            classes=classes
        )

    def _is_module_level(self, node: ast.FunctionDef) -> bool:
        """
        Vérifie si une fonction est définie au niveau du module.

        Args:
            node: Nœud AST de la fonction

        Returns:
            True si la fonction est au niveau module
        """
        for parent in ast.walk(self.tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.walk(parent):
                    if child is node:
                        return False
        return True

    def _extract_function_info(self, node: ast.FunctionDef) -> FunctionInfo:
        """
        Extrait les informations d'une fonction.

        Args:
            node: Nœud AST de la fonction

        Returns:
            FunctionInfo avec toutes les métadonnées
        """
        docstring = ast.get_docstring(node)
        source = self._get_source_code(node)
        dependencies = self._find_dependencies(node)

        return FunctionInfo(
            name=node.name,
            docstring=docstring,
            source_code=source,
            lineno=node.lineno,
            dependencies=dependencies
        )

    def _extract_class_info(self, node: ast.ClassDef) -> FunctionInfo:
        """
        Extrait les informations d'une classe.

        Args:
            node: Nœud AST de la classe

        Returns:
            FunctionInfo représentant la classe
        """
        docstring = ast.get_docstring(node)
        source = self._get_source_code(node)
        dependencies = self._find_dependencies(node)

        return FunctionInfo(
            name=node.name,
            docstring=docstring,
            source_code=source,
            lineno=node.lineno,
            dependencies=dependencies,
            is_class=True
        )

    def _get_source_code(self, node: ast.AST) -> str:
        """
        Extrait le code source d'un nœud AST.

        Args:
            node: Nœud AST

        Returns:
            Code source du nœud
        """
        # Utiliser ast.get_source_segment si disponible (Python 3.8+)
        try:
            return ast.get_source_segment(self.source_code, node)
        except AttributeError:
            # Fallback pour Python < 3.8
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
            return '\n'.join(self.source_lines[start_line:end_line])

    def _find_dependencies(self, node: ast.AST) -> Set[str]:
        """
        Trouve toutes les fonctions appelées dans un nœud.

        Args:
            node: Nœud AST à analyser

        Returns:
            Ensemble des noms de fonctions appelées
        """
        dependencies = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Fonction simple: func()
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                # Méthode: obj.method()
                elif isinstance(child.func, ast.Attribute):
                    dependencies.add(child.func.attr)

        return dependencies

    def get_function_dependencies_ordered(self, function_name: str,
                                         available_functions: Set[str]) -> List[str]:
        """
        Retourne les dépendances d'une fonction dans l'ordre topologique.

        Args:
            function_name: Nom de la fonction
            available_functions: Ensemble des fonctions disponibles dans le module

        Returns:
            Liste des noms de fonctions dépendantes, dans l'ordre à inclure dans le template
        """
        module_info = self.analyze()

        if function_name not in module_info.functions:
            return []

        func_info = module_info.functions[function_name]

        # Filtrer uniquement les dépendances qui sont des fonctions du module
        dependencies = func_info.dependencies & available_functions

        # Résoudre les dépendances récursivement
        ordered = []
        visited = set()

        def visit(fname: str):
            if fname in visited or fname == function_name:
                return
            visited.add(fname)

            if fname in module_info.functions:
                # Visiter d'abord les dépendances de cette fonction
                for dep in module_info.functions[fname].dependencies:
                    if dep in available_functions:
                        visit(dep)
                ordered.append(fname)

        for dep in dependencies:
            visit(dep)

        logger.debug(f"Dépendances de {function_name}: {ordered}")
        return ordered


def analyze_python_file(filepath: str) -> ModuleInfo:
    """
    Analyse un fichier Python et retourne les informations du module.

    Args:
        filepath: Chemin du fichier Python

    Returns:
        ModuleInfo avec toutes les informations extraites

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        SyntaxError: Si le fichier contient des erreurs de syntaxe
    """
    logger.info(f"Analyse du fichier: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        source_code = f.read()

    analyzer = FunctionAnalyzer(source_code)
    return analyzer.analyze()
