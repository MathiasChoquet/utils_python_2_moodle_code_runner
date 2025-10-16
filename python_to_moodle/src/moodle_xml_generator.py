"""
Module pour générer le XML Moodle CodeRunner.
Utilise xml.etree.ElementTree pour créer la structure XML.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MoodleTestCase:
    """Cas de test Moodle."""
    testcode: str
    expected: str
    stdin: str = ""
    extra: str = ""
    display: str = "SHOW"
    useasexample: int = 0
    testtype: int = 0
    hiderestiffail: int = 0
    mark: float = 1.0


@dataclass
class MoodleQuestion:
    """Question Moodle CodeRunner."""
    name: str
    questiontext: str
    template: str
    testcases: List[MoodleTestCase]
    answerpreload: str = ""
    defaultgrade: float = 1.0
    penalty: float = 0.0


class MoodleXMLGenerator:
    """Générateur de fichiers XML Moodle."""

    def __init__(self, config: dict):
        """
        Initialise le générateur avec la configuration.

        Args:
            config: Dictionnaire de configuration chargé depuis YAML
        """
        self.config = config

    def generate_quiz(self, questions: List[MoodleQuestion],
                     category_path: Optional[str] = None,
                     category_info: Optional[str] = None) -> ET.Element:
        """
        Génère un élément quiz complet avec catégorie et questions.

        Args:
            questions: Liste des questions à inclure
            category_path: Chemin de la catégorie (optionnel, sinon depuis config)
            category_info: Info de la catégorie (optionnel, sinon depuis config)

        Returns:
            Element racine <quiz>
        """
        logger.info(f"Génération du quiz avec {len(questions)} questions")

        # Créer l'élément racine
        quiz = ET.Element('quiz')

        # Ajouter la catégorie
        cat_path = category_path or self.config['category']['path']
        cat_info = category_info or self.config['category']['info']
        cat_info_format = self.config['category']['info_format']

        category_elem = self._create_category(cat_path, cat_info, cat_info_format)
        quiz.append(category_elem)

        # Ajouter les questions
        for question in questions:
            question_elem = self._create_question(question)
            quiz.append(question_elem)

        logger.info("Quiz généré avec succès")
        return quiz

    def _create_category(self, path: str, info: str, info_format: str) -> ET.Element:
        """
        Crée un élément catégorie.

        Args:
            path: Chemin de la catégorie
            info: Description de la catégorie
            info_format: Format du texte (html, moodle_auto_format)

        Returns:
            Element <question type="category">
        """
        question = ET.Element('question', type='category')
        ET.SubElement(question, 'category').append(
            self._create_text_element('text', path)
        )
        info_elem = ET.SubElement(question, 'info', format=info_format)
        info_elem.append(self._create_text_element('text', info))
        ET.SubElement(question, 'idnumber').text = ''

        return question

    def _create_question(self, question: MoodleQuestion) -> ET.Element:
        """
        Crée un élément question CodeRunner.

        Args:
            question: Objet MoodleQuestion

        Returns:
            Element <question type="coderunner">
        """
        logger.debug(f"Création de la question: {question.name}")

        q = ET.Element('question', type='coderunner')

        # Nom
        name_elem = ET.SubElement(q, 'name')
        name_elem.append(self._create_text_element('text', question.name))

        # Texte de la question
        qtext = ET.SubElement(q, 'questiontext', format='html')
        qtext.append(self._create_cdata_element('text', question.questiontext))

        # Feedback général
        feedback = ET.SubElement(q, 'generalfeedback', format='html')
        feedback.append(self._create_text_element('text', ''))

        # Paramètres de base
        ET.SubElement(q, 'defaultgrade').text = str(question.defaultgrade)
        ET.SubElement(q, 'penalty').text = str(question.penalty)
        ET.SubElement(q, 'hidden').text = '0'
        ET.SubElement(q, 'idnumber').text = ''

        # Paramètres CodeRunner depuis config
        cr_config = self.config['coderunner']
        ET.SubElement(q, 'coderunnertype').text = cr_config['type']
        ET.SubElement(q, 'prototypetype').text = str(cr_config['prototypetype'])
        ET.SubElement(q, 'allornothing').text = str(cr_config['allornothing'])
        ET.SubElement(q, 'penaltyregime').text = cr_config['penaltyregime']
        ET.SubElement(q, 'precheck').text = str(cr_config['precheck'])
        ET.SubElement(q, 'hidecheck').text = str(cr_config['hidecheck'])
        ET.SubElement(q, 'showsource').text = str(cr_config['showsource'])
        ET.SubElement(q, 'answerboxlines').text = str(cr_config['answerboxlines'])
        ET.SubElement(q, 'answerboxcolumns').text = str(cr_config['answerboxcolumns'])

        # Answer preload
        ET.SubElement(q, 'answerpreload').text = question.answerpreload or ''

        # Autres paramètres
        ET.SubElement(q, 'globalextra').text = ''
        ET.SubElement(q, 'useace').text = ''
        ET.SubElement(q, 'resultcolumns').text = ''

        # Template (CDATA directement, sans balise <text>)
        template_elem = ET.SubElement(q, 'template')
        template_elem.text = question.template

        # Paramètres template
        ET.SubElement(q, 'iscombinatortemplate').text = ''
        ET.SubElement(q, 'allowmultiplestdins').text = ''
        ET.SubElement(q, 'answer').text = ''
        ET.SubElement(q, 'validateonsave').text = str(cr_config['validateonsave'])
        ET.SubElement(q, 'testsplitterre').text = ''
        ET.SubElement(q, 'language').text = ''
        ET.SubElement(q, 'acelang').text = ''
        ET.SubElement(q, 'sandbox').text = ''
        ET.SubElement(q, 'grader').text = ''
        ET.SubElement(q, 'cputimelimitsecs').text = ''
        ET.SubElement(q, 'memlimitmb').text = ''
        ET.SubElement(q, 'sandboxparams').text = ''
        ET.SubElement(q, 'templateparams').text = ''
        ET.SubElement(q, 'hoisttemplateparams').text = str(cr_config['hoisttemplateparams'])
        ET.SubElement(q, 'extractcodefromjson').text = str(cr_config['extractcodefromjson'])
        ET.SubElement(q, 'templateparamslang').text = cr_config['templateparamslang']
        ET.SubElement(q, 'templateparamsevalpertry').text = str(cr_config['templateparamsevalpertry'])
        ET.SubElement(q, 'templateparamsevald').text = cr_config['templateparamsevald']
        ET.SubElement(q, 'twigall').text = str(cr_config['twigall'])
        ET.SubElement(q, 'uiplugin').text = ''
        ET.SubElement(q, 'uiparameters').text = ''
        ET.SubElement(q, 'attachments').text = '0'
        ET.SubElement(q, 'attachmentsrequired').text = '0'
        ET.SubElement(q, 'maxfilesize').text = '10240'
        ET.SubElement(q, 'filenamesregex').text = ''
        ET.SubElement(q, 'filenamesexplain').text = ''
        ET.SubElement(q, 'displayfeedback').text = str(cr_config['displayfeedback'])
        ET.SubElement(q, 'giveupallowed').text = str(cr_config['giveupallowed'])
        ET.SubElement(q, 'prototypeextra').text = ''

        # Test cases
        testcases_elem = ET.SubElement(q, 'testcases')
        for testcase in question.testcases:
            tc_elem = self._create_testcase(testcase)
            testcases_elem.append(tc_elem)

        # Tags
        tags_elem = ET.SubElement(q, 'tags')
        for tag in self.config.get('tags', []):
            tag_elem = ET.SubElement(tags_elem, 'tag')
            tag_elem.append(self._create_text_element('text', tag))

        return q

    def _create_testcase(self, testcase: MoodleTestCase) -> ET.Element:
        """
        Crée un élément testcase.

        Args:
            testcase: Objet MoodleTestCase

        Returns:
            Element <testcase>
        """
        tc = ET.Element(
            'testcase',
            testtype=str(testcase.testtype),
            useasexample=str(testcase.useasexample),
            hiderestiffail=str(testcase.hiderestiffail),
            mark=f"{testcase.mark:.7f}"
        )

        # Testcode
        testcode_elem = ET.SubElement(tc, 'testcode')
        testcode_elem.append(self._create_cdata_element('text', testcase.testcode))

        # Stdin
        stdin_elem = ET.SubElement(tc, 'stdin')
        stdin_elem.append(self._create_text_element('text', testcase.stdin))

        # Expected
        expected_elem = ET.SubElement(tc, 'expected')
        expected_elem.append(self._create_text_element('text', testcase.expected))

        # Extra
        extra_elem = ET.SubElement(tc, 'extra')
        extra_elem.append(self._create_text_element('text', testcase.extra))

        # Display
        display_elem = ET.SubElement(tc, 'display')
        display_elem.append(self._create_text_element('text', testcase.display))

        return tc

    def _create_text_element(self, tag: str, text: str) -> ET.Element:
        """Crée un élément texte simple."""
        elem = ET.Element(tag)
        elem.text = text if text else ''
        return elem

    def _create_cdata_element(self, tag: str, text: str) -> ET.Element:
        """
        Crée un élément avec CDATA.
        Note: ElementTree ne supporte pas directement CDATA,
        on l'ajoutera lors de la sérialisation.
        """
        elem = ET.Element(tag)
        elem.text = text if text else ''
        return elem

    def to_xml_string(self, quiz: ET.Element, pretty_print: bool = True) -> str:
        """
        Convertit l'élément quiz en string XML.

        Args:
            quiz: Element quiz
            pretty_print: Formater le XML avec indentation

        Returns:
            String XML
        """
        # Convertir en string sans échapper les entités HTML dans le contenu
        xml_str = ET.tostring(quiz, encoding='unicode', method='xml')

        # Wrapper les contenus en CDATA
        xml_str = self._wrap_cdata(xml_str)

        if pretty_print:
            # Pretty print manuel pour éviter l'échappement par minidom
            xml_str = self._manual_pretty_print(xml_str)

        # Ajouter la déclaration XML
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

        return xml_str

    def _wrap_cdata(self, xml_str: str) -> str:
        """
        Wrap certains contenus en CDATA et restaure les caractères échappés.

        Args:
            xml_str: String XML

        Returns:
            String XML avec CDATA
        """
        import re

        def wrap_text_if_needed(match):
            content = match.group(1)
            # Si le contenu contient du code Python, du HTML (échappé ou non), ou des templates Twig
            needs_cdata = any(marker in content for marker in [
                'def ', 'class ', 'import ', 'print(',
                '{{', '{%', 'SEPARATOR',
                '<p>', '<em>', '<strong>', '<div>',  # HTML non échappé
                '&lt;', '&gt;', '&amp;'  # HTML échappé
            ])

            if needs_cdata:
                # Restaurer les caractères échappés dans les CDATA
                content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                return f'<text><![CDATA[{content}]]></text>'
            return match.group(0)

        def wrap_template(match):
            content = match.group(1)
            # Restaurer les caractères échappés
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            return f'<template><![CDATA[{content}]]></template>'

        # Remplacer <template>...</template> SANS balise text interne
        xml_str = re.sub(r'<template>([^<].*?)</template>', wrap_template, xml_str, flags=re.DOTALL)

        # Remplacer les <text>...</text> qui contiennent du code
        xml_str = re.sub(r'<text>(.+?)</text>', wrap_text_if_needed, xml_str, flags=re.DOTALL)

        return xml_str

    def _manual_pretty_print(self, xml_str: str) -> str:
        """
        Pretty print manuel du XML pour préserver les CDATA.

        Args:
            xml_str: String XML

        Returns:
            XML formaté
        """
        import re

        # Utiliser minidom mais en préservant les CDATA
        try:
            # Remplacer temporairement les CDATA par des placeholders
            cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>', re.DOTALL)
            cdata_blocks = []

            def save_cdata(match):
                cdata_blocks.append(match.group(1))
                placeholder = f'__CDATA_{len(cdata_blocks)-1}__'
                logger.debug(f"Sauvegarde CDATA {len(cdata_blocks)-1}: {len(match.group(1))} caractères")
                return placeholder

            xml_temp = cdata_pattern.sub(save_cdata, xml_str)
            logger.debug(f"Total CDATA sauvegardés: {len(cdata_blocks)}")

            # Pretty print
            dom = minidom.parseString(xml_temp)
            xml_formatted = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('UTF-8')

            # Retirer la déclaration XML de minidom
            lines = xml_formatted.split('\n')
            if lines[0].startswith('<?xml'):
                xml_formatted = '\n'.join(lines[1:])

            # Restaurer les CDATA
            for i, cdata_content in enumerate(cdata_blocks):
                placeholder = f'__CDATA_{i}__'
                if placeholder in xml_formatted:
                    xml_formatted = xml_formatted.replace(
                        placeholder,
                        f'<![CDATA[{cdata_content}]]>'
                    )
                    logger.debug(f"CDATA {i} restauré")
                else:
                    logger.warning(f"CDATA {i} PERDU! Placeholder '{placeholder}' introuvable!")

            # Forcer le format <tag></tag> au lieu de <tag/>
            # On doit être prudent pour ne pas casser les attributs
            def replace_self_closing(match):
                tag_name = match.group(1)
                attributes = match.group(2).strip()
                if attributes:
                    return f'<{tag_name} {attributes}></{tag_name}>'
                else:
                    return f'<{tag_name}></{tag_name}>'

            xml_formatted = re.sub(r'<([\w:-]+)\s*([^/>]*?)\s*/>', replace_self_closing, xml_formatted)

            return xml_formatted

        except Exception as e:
            logger.warning(f"Erreur lors du pretty print: {e}")
            return xml_str

    def save_to_file(self, quiz: ET.Element, filepath: str):
        """
        Sauvegarde le quiz dans un fichier XML.

        Args:
            quiz: Element quiz
            filepath: Chemin du fichier de sortie
        """
        logger.info(f"Sauvegarde du quiz dans: {filepath}")

        xml_str = self.to_xml_string(quiz, pretty_print=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        logger.info(f"Quiz sauvegardé avec succès: {filepath}")
