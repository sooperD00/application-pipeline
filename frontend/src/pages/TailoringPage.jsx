/**
 * Tab 4: Tailoring
 *
 * Sprint 11 builds the real UI. Open design questions:
 * - see (ADR-014)
 * - Kickoff likely happens from Review tab, not here
 * - This page might be "review outputs" not "tailoring"
 * - Per-JD detail view vs. dashboard of all jobs?
 * - Human reviews one output at a time (don't mix up in your brain)
 * - "Download and open in Word" is the real end state, not in-app editing
 * - However, users may want to continue the conversation about this tailored resume output (and the optional cover letter and app questions) with claude with the same context he used to generate this output
 */
export default function TailoringPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-2">Tailoring</h1>
      <p className="text-pipeline-500">
        Tailoring jobs outputs, including opt-in cover letter and app questions if available.
        Download docx/individual files or a zip (docx, jd.txt, coverletter.txt, appquestions.txt, notes.txt). 
        Coming in Sprint 11.
      </p>
    </div>
  )
}
