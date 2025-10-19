#!/usr/bin/env python3
"""
Script principal pour transformer des fichiers Python + unittest en XML Moodle CodeRunner.

Usage:
    python python_to_moodle.py <fichier_fonctions.py> [options]

Exemple:
    python python_to_moodle.py input/partiel_In211_2526_with_comment.py
"""

import sys
import os
import logging
import argparse
from pathlib import Path
import yaml
import ast

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from function_analyzer import analyze_python_file, FunctionAnalyzer
from unittest_analyzer import analyze_unittest_file, validate_test_coverage
from assertion_transformer import AssertionTransformer
from moodle_xml_generator import (
    MoodleXMLGenerator,
    MoodleQuestion,
    MoodleTestCase
)

logger = logging.getLogger(__name__)


def setup_logging(config: dict):
    """
    Configure le système de logging.

    Args:
        config: Configuration du logging
    """
    log_level = getattr(logging, config['logging']['level'])
    log_format = config['logging']['format']
    log_file = config['logging'].get('file')

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )


def load_config(config_path: str) -> dict:
    """
    Charge la configuration depuis le fichier YAML.

    Args:
        config_path: Chemin du fichier de configuration

    Returns:
        Dictionnaire de configuration
    """
    logger.info(f"Chargement de la configuration: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def find_unittest_file(function_file: str) -> str:
    """
    Trouve le fichier unittest correspondant.

    Args:
        function_file: Chemin du fichier de fonctions

    Returns:
        Chemin du fichier unittest

    Raises:
        FileNotFoundError: Si le fichier unittest n'existe pas
    """
    # Le fichier unittest doit être nommé {nom}_unittest.py
    base_path = Path(function_file)
    unittest_file = base_path.parent / f"{base_path.stem}_unittest.py"

    if not unittest_file.exists():
        raise FileNotFoundError(
            f"Fichier unittest non trouvé: {unittest_file}\n"
            f"Le fichier unittest doit être nommé {base_path.stem}_unittest.py"
        )

    return str(unittest_file)


def build_template(dependencies: list, dependency_code: dict,
                   config: dict, imports: list = None) -> str:
    """
    Construit le template CodeRunner avec les dépendances.

    Args:
        dependencies: Liste des noms de fonctions dépendantes
        dependency_code: Dictionnaire {nom_fonction: code_source}
        config: Configuration
        imports: Liste des imports nécessaires (ex: ['import json'])

    Returns:
        Template complet
    """
    template_parts = []

    # Vérifier si on doit inclure les dépendances
    include_deps = config['template'].get('include_dependencies', True)

    if include_deps:
        # Ajouter les imports si nécessaires
        if imports:
            template_parts.extend(imports)
            template_parts.append('')  # Ligne vide

        # Ajouter les dépendances
        for dep_name in dependencies:
            if dep_name in dependency_code:
                template_parts.append(dependency_code[dep_name])
                template_parts.append('')  # Ligne vide entre les fonctions

    # Ajouter le template générique
    twig_template = config['template']['twig_template']
    template_parts.append(twig_template)

    template = '\n'.join(template_parts)

    # Nettoyer les retours chariot Windows (\r) pour n'avoir que \n
    template = template.replace('\r\n', '\n').replace('\r', '\n')

    return template


def detect_imports(module_info, function_name: str) -> list:
    """
    Détecte les imports nécessaires pour une fonction.

    Args:
        module_info: Information du module
        function_name: Nom de la fonction

    Returns:
        Liste des imports (ex: ['import json'])
    """
    imports = []

    # Vérifier si la fonction utilise json
    if function_name in module_info.functions:
        func_info = module_info.functions[function_name]
        if 'json' in func_info.source_code:
            imports.append('import json')

    return imports


def extract_dependencies_from_code(code: str, all_functions: set, all_classes: set) -> tuple:
    """
    Extrait les dépendances (fonctions et classes) depuis un code source.

    Args:
        code: Code source à analyser
        all_functions: Ensemble des noms de fonctions disponibles
        all_classes: Ensemble des noms de classes disponibles

    Returns:
        Tuple (set de fonctions, set de classes)
    """
    if not code:
        return set(), set()

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set(), set()

    func_deps = set()
    class_deps = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Appel de fonction
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in all_functions:
                    func_deps.add(func_name)
                elif func_name in all_classes:
                    class_deps.add(func_name)

    return func_deps, class_deps


def process_function(function_name: str, module_info, test_class,
                     config: dict, full_source_code: str) -> MoodleQuestion:
    """
    Traite une fonction et génère une question Moodle.

    Args:
        function_name: Nom de la fonction
        module_info: Informations du module
        test_class: Classe de test unittest
        config: Configuration
        full_source_code: Code source complet du module

    Returns:
        MoodleQuestion
    """
    logger.info(f"Traitement de la fonction: {function_name}")

    func_info = module_info.functions[function_name]

    # Construire le questiontext depuis le docstring
    if func_info.docstring:
        # Utiliser le docstring comme questiontext principal
        # Convertir le docstring en HTML (remplacer les sauts de ligne par <br>)
        docstring_html = func_info.docstring.replace('\n', '<br>\n')
        questiontext = f"<p>{docstring_html}</p>"
    else:
        # Fallback si pas de docstring
        questiontext = f"<p>Implémentez ci-dessous la fonction <em>{function_name}</em> demandée</p>"

    # Trouver les dépendances en analysant le module complet
    analyzer = FunctionAnalyzer(full_source_code)
    all_functions = set(module_info.functions.keys())
    all_classes = set(module_info.classes.keys())

    dependencies = analyzer.get_function_dependencies_ordered(function_name, all_functions)

    # Détecter les classes utilisées par la fonction et ses dépendances
    class_deps_set = set()

    # Classes utilisées directement par la fonction
    class_deps_set.update(func_info.dependencies & all_classes)

    # Classes utilisées par les fonctions dépendantes
    for dep_func_name in dependencies:
        if dep_func_name in module_info.functions:
            func_class_deps = module_info.functions[dep_func_name].dependencies & all_classes
            class_deps_set.update(func_class_deps)

    # Analyser aussi le setUp pour trouver les dépendances
    if test_class.setup_code:
        setup_func_deps, setup_class_deps = extract_dependencies_from_code(
            test_class.setup_code, all_functions, all_classes
        )
        # Ajouter les classes du setUp
        class_deps_set.update(setup_class_deps)
        # Ajouter les fonctions du setUp et résoudre leurs dépendances
        for setup_func in setup_func_deps:
            if setup_func not in dependencies and setup_func in module_info.functions:
                # Résoudre récursivement les dépendances de cette fonction
                sub_deps = analyzer.get_function_dependencies_ordered(setup_func, all_functions)
                dependencies.extend(sub_deps)
                if setup_func not in dependencies:
                    dependencies.append(setup_func)
                # Ajouter aussi les classes utilisées par cette fonction
                for sub_func in [setup_func] + sub_deps:
                    if sub_func in module_info.functions:
                        func_class_deps = module_info.functions[sub_func].dependencies & all_classes
                        class_deps_set.update(func_class_deps)

    # Résoudre les dépendances transitives des classes détectées
    # (fonctions utilisées par les classes)
    for class_dep in list(class_deps_set):
        if class_dep in module_info.classes:
            class_func_deps = module_info.classes[class_dep].dependencies & all_functions
            for func_dep in class_func_deps:
                if func_dep not in dependencies:
                    # Résoudre récursivement les dépendances de cette fonction
                    sub_deps = analyzer.get_function_dependencies_ordered(func_dep, all_functions)
                    for sub_dep in sub_deps:
                        if sub_dep not in dependencies:
                            dependencies.append(sub_dep)
                    dependencies.append(func_dep)
                    # Ajouter aussi les classes utilisées par cette fonction
                    if func_dep in module_info.functions:
                        func_class_deps = module_info.functions[func_dep].dependencies & all_classes
                        class_deps_set.update(func_class_deps)

    class_deps = list(class_deps_set)

    logger.debug(f"Dépendances de la fonction {function_name}: fonctions={dependencies}, classes={class_deps}")

    # Créer le dictionnaire de code des dépendances (classes + fonctions)
    dependency_code = {}

    # Ajouter les classes dépendantes en premier
    for class_dep in class_deps:
        dependency_code[class_dep] = module_info.classes[class_dep].source_code

    # Puis ajouter les fonctions
    for func_dep_name in dependencies:
        dependency_code[func_dep_name] = module_info.functions[func_dep_name].source_code

    # Détecter les imports nécessaires
    imports = detect_imports(module_info, function_name)

    # Vérifier aussi dans les dépendances
    for dep_name in dependencies + class_deps:
        if dep_name in module_info.functions and 'json' in module_info.functions[dep_name].source_code:
            if 'import json' not in imports:
                imports.append('import json')
        if dep_name in module_info.classes and 'json' in module_info.classes[dep_name].source_code:
            if 'import json' not in imports:
                imports.append('import json')

    # Construire le template avec l'ordre correct: classes puis fonctions
    dependencies_ordered = class_deps + dependencies
    template = build_template(dependencies_ordered, dependency_code, config, imports)

    # Transformer les tests unittest en test cases Moodle
    transformer = AssertionTransformer()
    testcases = []

    for i, test_method in enumerate(test_class.methods):
        try:
            moodle_test = transformer.transform_test_method(
                test_method.source_code,
                test_class.setup_code
            )

            testcase = MoodleTestCase(
                testcode=moodle_test.testcode,
                expected=moodle_test.expected,
                useasexample=1 if test_method.is_first else 0,
                display=config['testcase']['display'],
                testtype=config['testcase']['testtype'],
                hiderestiffail=config['testcase']['hiderestiffail'],
                mark=config['testcase']['mark']
            )
            testcases.append(testcase)
            logger.debug(f"Test case créé: {test_method.name}")

        except Exception as e:
            logger.error(f"Erreur lors de la transformation du test {test_method.name}: {e}")
            raise

    # Créer la question
    question = MoodleQuestion(
        name=function_name,
        questiontext=questiontext,
        template=template,
        testcases=testcases,
        defaultgrade=config['coderunner']['defaultgrade'],
        penalty=config['coderunner']['penalty']
    )

    logger.info(f"Question créée pour {function_name} avec {len(testcases)} tests")
    return question


def process_class(class_name: str, module_info, test_class,
                  config: dict, full_source_code: str) -> MoodleQuestion:
    """
    Traite une classe et génère une question Moodle.

    Args:
        class_name: Nom de la classe
        module_info: Informations du module
        test_class: Classe de test unittest
        config: Configuration
        full_source_code: Code source complet du module

    Returns:
        MoodleQuestion
    """
    logger.info(f"Traitement de la classe: {class_name}")

    class_info = module_info.classes[class_name]

    # Construire le questiontext depuis le docstring
    if class_info.docstring:
        # Utiliser le docstring comme questiontext principal
        # Convertir le docstring en HTML (remplacer les sauts de ligne par <br>)
        docstring_html = class_info.docstring.replace('\n', '<br>\n')
        questiontext = f"<p>{docstring_html}</p>"
    else:
        # Fallback si pas de docstring
        questiontext = f"<p>Implémentez ci-dessous la classe <em>{class_name}</em> demandée</p>"

    # Trouver les dépendances en analysant le module complet
    analyzer = FunctionAnalyzer(full_source_code)
    all_functions = set(module_info.functions.keys())
    all_classes = set(module_info.classes.keys())

    # Pour une classe, chercher les dépendances directes
    direct_deps = class_info.dependencies & all_functions

    # Résoudre récursivement les dépendances des fonctions
    all_deps_ordered = []
    visited_funcs = set()
    class_deps_set = set()

    def resolve_function_deps(func_name):
        """Résout récursivement les dépendances d'une fonction."""
        if func_name in visited_funcs or func_name not in all_functions:
            return
        visited_funcs.add(func_name)

        # D'abord résoudre les dépendances de cette fonction
        func_deps = module_info.functions[func_name].dependencies & all_functions
        for dep in func_deps:
            resolve_function_deps(dep)

        # Aussi collecter les classes utilisées par cette fonction
        func_class_deps = module_info.functions[func_name].dependencies & all_classes
        class_deps_set.update(func_class_deps)

        # Puis ajouter la fonction elle-même
        all_deps_ordered.append(func_name)

    # Résoudre les dépendances pour chaque fonction directement utilisée
    for dep in direct_deps:
        resolve_function_deps(dep)

    # Ajouter également les classes directement dépendantes (sauf la classe courante)
    for dep in class_info.dependencies:
        if dep in all_classes and dep != class_name:
            class_deps_set.add(dep)

    # Convertir en liste ordonnée (exclure la classe courante)
    class_deps = [c for c in class_deps_set if c != class_name]

    logger.debug(f"Dépendances de la classe {class_name}: fonctions={all_deps_ordered}, classes={class_deps}")

    # Créer le dictionnaire de code des dépendances (fonctions + classes)
    dependency_code = {}

    # Ajouter les classes dépendantes en premier
    for class_dep in class_deps:
        dependency_code[class_dep] = module_info.classes[class_dep].source_code

    # Puis ajouter les fonctions
    for func_name in all_deps_ordered:
        dependency_code[func_name] = module_info.functions[func_name].source_code

    # Détecter les imports nécessaires
    imports = []
    if 'json' in class_info.source_code:
        imports.append('import json')

    # Vérifier aussi dans les dépendances
    for dep_name in all_deps_ordered + class_deps:
        if dep_name in module_info.functions and 'json' in module_info.functions[dep_name].source_code:
            if 'import json' not in imports:
                imports.append('import json')
        if dep_name in module_info.classes and 'json' in module_info.classes[dep_name].source_code:
            if 'import json' not in imports:
                imports.append('import json')

    # Construire le template avec l'ordre correct: classes puis fonctions
    dependencies_ordered = class_deps + all_deps_ordered
    template = build_template(dependencies_ordered, dependency_code, config, imports)

    # Transformer les tests unittest en test cases Moodle
    transformer = AssertionTransformer()
    testcases = []

    for i, test_method in enumerate(test_class.methods):
        try:
            moodle_test = transformer.transform_test_method(
                test_method.source_code,
                test_class.setup_code
            )

            testcase = MoodleTestCase(
                testcode=moodle_test.testcode,
                expected=moodle_test.expected,
                useasexample=1 if test_method.is_first else 0,
                display=config['testcase']['display'],
                testtype=config['testcase']['testtype'],
                hiderestiffail=config['testcase']['hiderestiffail'],
                mark=config['testcase']['mark']
            )
            testcases.append(testcase)
            logger.debug(f"Test case créé: {test_method.name}")

        except Exception as e:
            logger.error(f"Erreur lors de la transformation du test {test_method.name}: {e}")
            raise

    # Créer la question
    question = MoodleQuestion(
        name=class_name,
        questiontext=questiontext,
        template=template,
        testcases=testcases,
        defaultgrade=config['coderunner']['defaultgrade'],
        penalty=config['coderunner']['penalty']
    )

    logger.info(f"Question créée pour {class_name} avec {len(testcases)} tests")
    return question


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description='Transforme des fichiers Python en questions Moodle CodeRunner XML'
    )
    parser.add_argument(
        'function_file',
        help='Fichier Python contenant les fonctions à transformer'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Fichier de configuration YAML (défaut: config.yaml)'
    )
    parser.add_argument(
        '--unittest-file',
        help='Fichier unittest (optionnel, auto-détecté si non fourni)'
    )
    parser.add_argument(
        '--output',
        help='Fichier XML de sortie (optionnel, auto-généré si non fourni)'
    )

    args = parser.parse_args()

    # Charger la configuration
    try:
        config = load_config(args.config)
        setup_logging(config)
    except Exception as e:
        print(f"ERREUR: Impossible de charger la configuration: {e}", file=sys.stderr)
        return 1

    logger.info("=== Démarrage de la transformation Python → Moodle XML ===")

    try:
        # Trouver le fichier unittest
        unittest_file = args.unittest_file or find_unittest_file(args.function_file)
        logger.info(f"Fichier de fonctions: {args.function_file}")
        logger.info(f"Fichier unittest: {unittest_file}")

        # Lire le code source complet du fichier
        with open(args.function_file, 'r', encoding='utf-8') as f:
            full_source_code = f.read()

        # Analyser le fichier de fonctions
        module_info = analyze_python_file(args.function_file)
        logger.info(f"Module analysé: {len(module_info.functions)} fonctions, {len(module_info.classes)} classes trouvées")

        # Analyser le fichier unittest
        test_classes = analyze_unittest_file(unittest_file)
        logger.info(f"Tests analysés: {len(test_classes)} classes de test trouvées")

        # Valider la couverture des tests
        function_names = list(module_info.functions.keys())
        class_names = list(module_info.classes.keys())
        all_names = function_names + class_names
        validate_test_coverage(all_names, test_classes)

        # Générer les questions Moodle pour les fonctions
        questions = []
        for function_name in function_names:
            if function_name in test_classes:
                question = process_function(
                    function_name,
                    module_info,
                    test_classes[function_name],
                    config,
                    full_source_code
                )
                questions.append(question)

        # Générer les questions Moodle pour les classes
        for class_name in class_names:
            if class_name in test_classes:
                question = process_class(
                    class_name,
                    module_info,
                    test_classes[class_name],
                    config,
                    full_source_code
                )
                questions.append(question)

        # Générer le XML
        generator = MoodleXMLGenerator(config)
        quiz = generator.generate_quiz(
            questions,
            category_info=module_info.docstring
        )

        # Déterminer le fichier de sortie
        if args.output:
            output_file = args.output
        else:
            base_name = Path(args.function_file).stem
            output_file = f"output/{base_name}_moodle.xml"

        # Créer le répertoire output s'il n'existe pas
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        # Sauvegarder
        generator.save_to_file(quiz, output_file)

        logger.info("=== Transformation terminée avec succès ===")
        logger.info(f"Fichier généré: {output_file}")
        logger.info(f"Questions créées: {len(questions)}")

        return 0

    except Exception as e:
        logger.error(f"ERREUR: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
