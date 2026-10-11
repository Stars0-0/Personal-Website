# Kristan Martinez, portfolio

I'm a computer science student at the University of the West Indies, St. Augustine (class of 2027), heading toward AI engineering and data analysis. This repo is my portfolio site and the small backend behind it.

**Live site:** https://stars0-0.github.io/Personal-Website/

The site is one static page with an interactive terminal at the top. Type `help` to look around: `about`, `projects`, `skills`, `contact` and `try` all work, with command history on the arrow keys and Tab completion. Two small demos let you run the ideas behind my projects instead of reading about them. When the backend is connected, the terminal can also take a guestbook note (`sign`), a private message (`message`) and show a visit counter (`stats`).

## What's on the site

- **Skill matcher.** A JavaScript version of my Python recommender. Pick skills, and it ranks 7 made-up job roles with TF-IDF weights and cosine similarity. Rare skills such as PyTorch count for more than common ones such as Python.
- **KNN playground.** Click or drag a point on the chart and change k to watch the vote change. Even values of k can tie, and the nearest neighbour breaks the tie.
- **Projects, experience and skills**, each written for someone skimming it.

## Projects

| Project | Stack | What it is |
|---|---|---|
| AI recommendation engine | Python, TF-IDF, cosine similarity | Matches a user's skills to job roles. TF-IDF gives specific skills more weight than generic ones, and cosine similarity ranks the roles. |
| ML classification pipeline | Python, scikit-learn, pandas | An end-to-end KNN classifier: standardized features, an 80/20 split, an automatic choice of K, and a confusion matrix and F1 score instead of accuracy alone. |
| Rule-based chatbot | Python | A three-tier conversation engine that answers from dictionary lookups instead of long if/elif chains, with multi-keyword matching and input sanitizing. |
| [PennyPilot](https://github.com/Clockwork-Studios-Technologies-Limited/PennyPilot) | FastAPI, SQLModel, PostgreSQL, Docker | A finance web app built by five contributors. I worked on web design and budget changes. |
| Rhythm 5 | React, Vite, TypeScript, Tailwind CSS | A cyberpunk rhythm game in the browser with 12 mini-games and a synthesizer built on the Web Audio API. |
| [School management system](https://github.com/Stars0-0/School-Management-System) | Java, Swing | A desktop app for managing students and teachers, built on an abstract `Person` class, subclasses and a `Gradeable` interface. |
| [Task manager](https://github.com/Stars0-0/cli-task-manager) and [file organizer](https://github.com/Stars0-0/file-organizer-script) | Python | A JSON-backed command-line task manager, and a script that sorts a folder by file type with `os` and `shutil`. |

I also run a self-hosted Linux lab to practice system administration and networking. In July 2026 I was a student mentor at the UWI AI-Builders Boot Camp, helping groups through generative AI concepts.

## How it's built

```
visitor's browser
   |-- page ------------------> GitHub Pages    index.html
   '-- terminal commands -----> Render          portfolio-api/ (FastAPI)
                                    '---------> Neon    (Postgres)
```

- **Frontend:** plain HTML, CSS and JavaScript in a single file. No framework and no build step. Its only outside dependency is two Google Fonts, plus the backend when it's connected.
- **Backend:** [`portfolio-api/`](portfolio-api/), a FastAPI and SQLModel service with a moderated guestbook, a private inbox, token-protected admin routes, input validation, a CORS allow-list and a rate limit. Its README explains each design choice.
- **Hosting:** GitHub Pages, Render and Neon, all on free plans.

## Quality checks

- **Accessibility:** axe-core reported no violations at 390 px and 1366 px wide. Every control works from the keyboard, and reduced-motion settings are respected.
- **Demo maths:** I compared both demos against an independent Python implementation, and they agree.
- **Terminal safety:** anything a visitor types is escaped before it's shown, so input is displayed as text and never run.
- **Backend tests:** 6 pytest checks cover validation, moderation, admin auth, the rate limit, the counter and CORS. They run against SQLite and against Postgres.

## Run it

- **Site:** open `index.html` in a browser. With no backend connected, the backend commands stay hidden.
- **Backend:** see [`portfolio-api/README.md`](portfolio-api/README.md).

## Contact

kristan944@gmail.com, [LinkedIn](https://linkedin.com/in/kristan-martinez-3964921b8), [GitHub](https://github.com/Stars0-0)
