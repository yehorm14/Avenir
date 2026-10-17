# Labelling task: the matcher's test set (30 minutes, 2-3 people)

This is the set the interest matcher is graded on. It's what stops us from fooling ourselves, so **don't look at the matcher's code, tags or keyword lists before writing.**

## What to do

1. Open `labels_template.csv` and copy it to `labels_<yourname>.csv`.
2. Write **about 20 rows each**. Each row is a short "what I enjoy" text, written the way a different 16-18-year-old would say it:
   - Vary the voice: chatty, vague, very specific, unsure, one line, three lines.
   - Include a few hard ones: "I like helping people but hate blood", "good at maths but find it boring", "no idea, I like gaming and football".
   - Don't name a job title in the text (that makes it too easy).
3. For each text, pick the **3 best-fitting careers** from the list below, best first, using the SOC code. Leave a slot empty if fewer than 3 really fit.
4. Optionally add a note on why.

## Careers to choose from (the 20 demo careers)

| SOC | Career |
| --- | --- |
| 2134 | Software developer |
| 3544 | Data analyst |
| 2133 | IT business analyst or systems designer |
| 2135 | Cyber security professional |
| 2141 | Web designer |
| 2142 | Graphic and multimedia designer |
| 2451 | Architect |
| 2452 | Architectural technologist or planner |
| 3120 | CAD and architectural technician |
| 2121 | Civil engineer |
| 2123 | Electrical engineer |
| 3113 | Engineering technician |
| 2453 | Quantity surveyor |
| 2454 | Chartered surveyor |
| 2433 | Actuary, economist or statistician |
| 2422 | Finance and investment analyst |
| 2421 | Accountant |
| 2254 | Medical radiographer |
| 5241 | Electrician |
| 2313 | Secondary school teacher |

## What happens next

Arsenii's script splits the rows at random (fixed seed) into a development set (40%), used for building, and a test set (60%), scored **once** at the end. The headline metric is top-3 hit rate: does at least one of your 3 careers appear in the matcher's top 3? Keyword search, off-the-shelf embeddings and the fine-tuned model are compared on the same test set, and a model ships only if it beats the simpler one.
