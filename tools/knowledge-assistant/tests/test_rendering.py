from atom_knowledge.rendering import render_answer
from atom_knowledge.cli import parser


def test_readable_answer_keeps_synthesis_separate_and_cited():
    answer = {'insufficient_evidence': False,
              'inferences': [{'text': 'Interpretação fundamentada.', 'citations': ['S1']}],
              'facts': [{'citation': 'S1', 'quote': 'Exact evidence.'}],
              'citations': [{'citation': 'S1', 'source_path': 'docs/source.md', 'locator': 'lines:2-4'}]}
    rendered = render_answer(answer)
    assert 'Síntese do modelo' in rendered and 'Trechos das fontes' in rendered
    assert 'Interpretação fundamentada. [S1]' in rendered
    assert 'docs/source.md (lines:2-4)' in rendered


def test_absence_never_prints_unrelated_evidence():
    value = render_answer({'insufficient_evidence': True, 'missing_identifiers': ['P9999'], 'generation_error': None})
    assert 'P9999' in value and 'insuficientes' in value
    assert 'Referências' not in value


def test_cli_supports_explicit_machine_output():
    assert parser().parse_args(['ask', 'P014']).format == 'text'
    assert parser().parse_args(['ask', 'P014', '--format', 'json']).format == 'json'
