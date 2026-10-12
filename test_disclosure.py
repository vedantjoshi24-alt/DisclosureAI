import unittest
from io import BytesIO

from pypdf import PdfWriter

from disclosure import generate_disclosure, natural_list, validate_inputs
from document_review import DocumentReviewError, analyze_document_text, extent_from_scope, review_pdf


class DisclosureTests(unittest.TestCase):
    def test_generates_a_single_use_disclosure(self):
        statement = generate_disclosure(
            "Data Structures Report",
            ["Coding"],
            "I used it to explain a sorting algorithm and identify a bug.",
            "Limited",
        )
        self.assertIn("Data Structures Report", statement)
        self.assertIn("coding", statement)
        self.assertIn("limited", statement.lower())

    def test_multiple_uses_have_natural_grammar(self):
        statement = generate_disclosure(
            "Research Proposal",
            ["Brainstorming", "Research", "Editing"],
            "I used it to suggest topic directions and improve sentence clarity.",
            "Moderate",
        )
        self.assertIn("brainstorming, research, and editing", statement)

    def test_other_assistance_is_resolved(self):
        statement = generate_disclosure(
            "Literature Review",
            ["Other"],
            "I used it to translate a short note into English.",
            "Limited",
            "translation support",
        )
        self.assertIn("translation support", statement)
        self.assertNotIn("for Other", statement)

    def test_validation_requires_key_fields(self):
        errors = validate_inputs("", [], "short", "Unknown")
        self.assertEqual(set(errors), {"project_name", "assistance_types", "description", "extent"})

    def test_validation_requires_other_detail(self):
        errors = validate_inputs(
            "AI Report", ["Other"], "I used it to translate selected course notes.", "Limited", ""
        )
        self.assertIn("other_assistance", errors)

    def test_generation_is_deterministic_and_normalizes_whitespace(self):
        args = (
            "  AI   Report  ",
            ["Summarization", "Editing"],
            "I used it to   condense notes\n and improve grammar.",
            "Substantial",
        )
        self.assertEqual(generate_disclosure(*args), generate_disclosure(*args))
        self.assertIn("AI Report", generate_disclosure(*args))
        self.assertEqual(natural_list(["a", "b"]), "a and b")

    def test_document_review_reports_structure_without_claiming_ai_use(self):
        insights = analyze_document_text(
            "INTRODUCTION\n\ndef sort_items(values):\n    return values\n\n"
            "REFERENCES\n",
            "assignment.pdf",
            2,
        )
        self.assertTrue(insights.code_like_content)
        self.assertTrue(insights.references_section)
        self.assertIn("Code-like structure was found.", insights.observations)
        self.assertNotIn("AI", " ".join(insights.observations))

    def test_extent_suggestion_requires_student_self_assessment(self):
        self.assertEqual(extent_from_scope("Several described tasks or sections"), "Moderate")
        self.assertIsNone(extent_from_scope("Not sure - choose manually"))

    def test_blank_pdf_has_no_text_but_is_handled(self):
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        memory_pdf = BytesIO()
        writer.write(memory_pdf)
        insights = review_pdf(memory_pdf.getvalue(), "blank.pdf")
        self.assertFalse(insights.text_detected)
        self.assertEqual(insights.page_count, 1)

    def test_invalid_pdf_is_rejected(self):
        with self.assertRaises(DocumentReviewError):
            review_pdf(b"", "empty.pdf")


if __name__ == "__main__":
    unittest.main()
