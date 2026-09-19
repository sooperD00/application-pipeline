# ADR-014: Application Package — Zip Download per Tailoring Job

**Date**: 2026-03-07
**Status**: Accepted (shipped Sprint 11)

**Decision**: Add a zip download endpoint that bundles all outputs for a single tailoring job into one file. The user gets a ready-to-use folder they can open in their file manager and work from.

**Contents of the zip**:

```
CompanyName_RoleName/
  resume.docx                  ← output_resume_docx (the tailored resume)
  jd.txt                       ← cleaned_text + metadata (company, role, link, compensation)
  cover_letter.txt             ← output_cover_letter (omitted if not requested)
  app_questions.txt            ← output_app_answers (omitted if no questions)
  analysis.txt                 ← analysis_text + requirements_met (Claude's fit assessment)
  notes.txt                    ← placeholder for the human to add notes after download
```

**Rationale**: The current workflow after tailoring is: download the docx, then mentally reconstruct which JD it was for, then go find the cover letter text in the app, then copy-paste app answers somewhere. That's 4 trips to the app for one application submission. The zip bundles everything the human needs to sit down and apply — open the folder, review the resume in Word, paste the cover letter, paste app answers, and move on.

`notes.txt` ships empty with a header line (company, role, date). It's where the human jots "submitted 3/8, heard back 3/12, phone screen scheduled 3/15" — a portable paper trail that lives with the application files even if the app is offline. This becomes more useful when Activity tracking is built (Phase 1), but the file is free to include now.

The txt files are plain text, not markdown or docx, because the user is pasting them into web forms on application sites. No formatting to strip.

**Endpoint**: `GET /api/jds/{id}/tailoring/{job_id}/package` — returns a zip. Sits next to the existing `/docx` endpoint. Backend assembles the zip in memory using Python's `zipfile` module (no temp files, no disk writes). The zip is small (~50-100KB for text + one docx).

**What this needs**: One new endpoint in `jds.py`, ~40 lines. No new models, no migrations, no new services. All data is already in TailoringJob + JD rows. Shipped in Sprint 11.

**Alternatives considered**:
- Frontend-assembled zip (JSZip library, multiple fetch calls): works but slower, adds a JS dependency, and the frontend has to know the file layout. Backend already has all the data in one query.
- Individual download buttons per file: forces the user to click 4-5 times and organize the files themselves. Defeats the purpose.
- Include raw_text alongside cleaned_text: adds noise. The cleaned version is what Claude analyzed. Raw is available in-app via "view raw" toggle if needed.
