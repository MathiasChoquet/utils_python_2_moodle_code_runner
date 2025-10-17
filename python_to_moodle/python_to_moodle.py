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

    return '\n'.join(template_parts)


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
    questiontext = f"<p>Implémentez ci-dessous la fonction <em>{function_name}</em> demandée</p>"
    if func_info.docstring:
        # Optionnel: ajouter le docstring dans le questiontext
        # questiontext += f"<pre>{func_info.docstring}</pre>"
        pass

    # Trouver les dépendances en analysant le module complet
    analyzer = FunctionAnalyzer(full_source_code)
    all_functions = set(module_info.functions.keys())
    dependencies = analyzer.get_function_dependencies_ordered(function_name, all_functions)

    # Créer le dictionnaire de code des dépendances
    dependency_code = {
        name: module_info.functions[name].source_code
        for name in dependencies
    }

    # Détecter les imports nécessaires
    imports = detect_imports(module_info, function_name)

    # Construire le template
    template = build_template(dependencies, dependency_code, config, imports)

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
        logger.info(f"Module analysé: {len(module_info.functions)} fonctions trouvées")

        # Analyser le fichier unittest
        test_classes = analyze_unittest_file(unittest_file)
        logger.info(f"Tests analysés: {len(test_classes)} classes de test trouvées")

        # Valider la couverture des tests
        function_names = list(module_info.functions.keys())
        validate_test_coverage(function_names, test_classes)

        # Générer les questions Moodle
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
