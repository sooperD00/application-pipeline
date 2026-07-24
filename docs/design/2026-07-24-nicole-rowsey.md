---
from: Greg Rowsey
date: 2026-07-20
against: v1.0
ask: 2026-03-15-beta-invite
context: saw a walkthrough, responding like a PM
---

# Walk Through

Greg says: "OK I maybe see kind of what you are doing but... I'm thinking...
Greg is *onboarding* -> what is the 1st step?"

> Decision: let's start with onboarding
> Deferred: mature candidate with funnel analysis, interviews with Segno, record yourself and get analysis; etc etc etc.

> Goal:
   - give users as seamless a transfer between job search stages as possible
   - on as few iterations between them and the platform as possible
   - give them quick deliverables *at each click or turn* (a score, top 5 titles, skills) so they are *motivated to finish the onboarding*
   - then deliver them *a valuable artifact* so that they *save their profile and continue with the "free trial"*


# Platform Differentiator

What do users want? (...and why do exiting tools suck)

Greg says: "I think the benefit is that... AI gives you
   - generic data: what are the skills of *all* product managers
   - plus locally personally optimized data: and is top 5 on resume?"

> Decision: onboard with resume + questions + job matching

# User flow

1. Onboard Options: just upload resumes | build your vault.
2. Profile Interation: Answer a few questions, get a score, get an optimized resume.
3. Real jobs to match: Now give us some jobs you want. We'll run the analysis.

# Methodology

How do we do this with managed API calls and schema derived from
people's onboarding input?

Personal Job Seeker Data Intake -> Schema Extraction -> Job Title Feed Forward

Everybody's entrypoing is different but let's start somewhere. What could intake look like:
   - Greg *has* a resume
      - so his entry point is upload a resume
   - Other people might 
      - have a bunch of resumes -> extract into schema one at a time? max how many?
      - really out of date material -> what questions do we ask them
      - just a LinkedIn or other profile
      - nothing

Process:
   - Input a wide range of starting points -- unlocks features like the web crawler
      - upload docs
      - paste text
      - answer pre-defined questions (state-table style)
   - break up personal job seeker info into a schema optimized for *all* the job search activities and skills needed through the whole job search pipeline
   - Just upload up to 3 resumes and run the matcher with manual JD text scrapes   

Output: "your Vault"
   - genericized data classes that can fit ~any job seeker type
   - metadata so you can refine your search with funnel analysis
   - your info stored in there in a generic way such that...

Feed Forward:
   - this "vault" provides the fundamental info for *all* job seeking phases
      - that an LLM can use to match you to JDs *that you would match highly to* if you *were* to tailor your resume (the better-than-just-semantic match)
      - to write cover letters or answer application questions for you "in your voice" (because you typed some of this text)
      - to add details that got cut from the resume but that belong in interview practice simulations and prep docs
      - that an LLM can use to give meta analysis on how to improve your skills, writing, process, practice, whatever to help your job seeking


# "The" Pipeline

Ok great. But what is this "pipeline," why are you calling it that, and why did you choose it this way?

Answer: because of the brutal realities of 1) the funnel itself 2) how data *is already stored* about open jobs, which are the only ones you're likely to get with a platform instead of "knowing a guy."

TODO: some kinda summary of of the pipeline here

## Stage 1. What am I? (Job Title You Want / Know + Suggestions) and Building Your Vault

Unfortunately, you ~are your job title(s). Let me explain why.

Consider that ~all possible jobs out there are in 3 groups:
   1) jobs you make up yourself and self-employ yourself with
   2) jobs other people make up for you because you know them and they trust you 
   3) actually posted jobs  <-- *a data platform can only help you with these*

So then let's continue with only the category of "actually posted jobs" which I'll call "open JDs." Jobs are posted "on the interwebs" or "in the cloud" or "on a website" -> they exist as ~text in a computer that is connected to the internet. Job boards like LinkedIn and websites like individual companies posting their own jobs store that ~text as structured data, and it is almost univerally *keyed by job title or role,* plus an internal job id number that is not initially useful to us as job seekers. The reason for this is that it's really hard to define what jobs are. People have tried (see the BLS categories that we have targeted in our initial onboarding development phase). But in the end you have to call a job, and, unfortunately, a person, *something*. "Title" or "Role" is the best we've got.

Quick win: Answer a few qeustions, get a score, get an optimized resume.
   - Input your resume and your desired job title and get a score. Answer: am I crazy? easy optimize? applyk now? or big rewrite? ... even maybe different roles?
   - what's expensive? do I keep going with the tool?

Funnel:
   - "all" jobs -> ~1_000 to ~10_000 jobs
   - because REGEX on a key is cheap

Problem:
   - what roles to I "want"?
   - what do I need to do that role (~mandatory skills)?
   - am I branded this way online (e.g. LinkedIn profile)?

Process:
   - user inputs docs or text
   - claude feeds back into structured schema and recommends questions to ask the user (from a set list I think)
   - fields are exposed to user (top level initialy on page, but can drill down)
   - user can "refesh" (a button click) categorization, "refesh with objection" (text box), or "add my own" (e.g. I know I want job title = some_title)
   - iterate until user likes the data and options

Prompt:
   - reference "What 10 job titles does my resume scream to you?"

Outputs:
   - up to 5 job titles
   - fit criteria for each job title
   - resume score based on the titles and title fit criteria
   - low/med/high fit score for each desired title
   - top 1-5 skills / experiences that would improve score the most?
   
Success Criteria: iterate until...
   - user agrees with the titles and fit criteria
   - fit score on at least 1 job title is high enough to expect reasonable results in next phases

Artifacts:
   - LinkedIn profile
   - generic resume

Feed Forward:
   - ~5 titles to search "all" jobs -> ~1_000 to ~10_000 jobs
   - user experience/skill vault dataset

Test Vehicle:
   - python script: ingest input -> input text + prompt -> claude API call -> claude classifies -> human review with html viewer -> adjust -> repeat
   - integrate and deploy when: ???


## Stage 2a. My first open job match?

This stage is similar to Stage 2, but it is designed as a mini-match phase during the onboarding process only. It gives the user only 1 JD to peruse (or possibly 1 per "locked in" job title), for the purpose of *them iterating on personal input,* not necessarily finding something to apply to. It's basically a check of claude taking what they inputted, using it in the structured extraction form, then grabbing somethign with that title and holding it up to the user and saying... "like this?" (yes|no)... "like this?" (yes|no). That way I don't have to hit the claude api intensively in the batch search if they don't even like the possibilities. But maybe this isn't a good thing... maybe this will turn users off... maybe I should just do the 25 because users might get frustrated (you said "software engineer" and I'm pulling frontend but you're backend? we ain't gonna match... not sure if this is good one at a time or if the meta analysis on 25 will be best). We can test and see... we don't know yet. But this could be a chicken and egg problem...

But the idea is to show them 1 JD and *how this tool scores against it*. So even if they don't get the throughput benefit of the 25-in-a-batch, they can see how the tool works.

Prompt:
   - turn 1: expand the JD language with company / role info and analysis
   - turn 2: list out the requirements (explicit and implicit) and rank the candidate against the requirements; provide a rough matching score in percent. Shows the chart and explains itself pretty well.


## Stage 2. How do I find open jobs

Funnel:
   - ~1000s of jobs -> ~100s of jobs

Process:
   - web crawl with title REGEX (slow but hands-off)
   - or paste jds strategy (immediate but hands-on))
      - this lets LinkedIn or other job board do the REGEX and whatever other ML or other advanced matching it does on its own platform. You're bringing it here to let a tool read the vast numbers of "matches" (plus ads plus recruiting firms) that LinkedIn so generously delivers you.

Success criteria:
   - Do the tools return 25 JDs that *you* find acceptable to look into / spend time reading on any given day? You don't have to read them all the time — that's the point of phase 3. But to *tune* this step, that's how you test this.

## Stage 3. **What open jobs do *I* apply to**

Funnel: 
   - ~100s of jobs -> ~10 per week

Process:
   - batched matcher with meta analysis
   - apply to top ~10, optimizing application materials for *each* JD
   - review recommended skills, projects, input
      
## Stage 4. 

Mature candiate?
Funnel Analysis
Upload your old spreadsheet so you can track from the beginning



