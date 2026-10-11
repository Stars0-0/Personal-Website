# Kristan Martinez, portfolio

Live site: https://stars0-0.github.io

A single-file portfolio built with plain HTML, CSS and JavaScript. No framework, no build step, no dependencies beyond two Google Fonts.

## What's in it

- **Interactive terminal.** Type `help`. Commands, history (arrow keys) and Tab completion all work. With the backend connected, visitors can also type `sign` to leave a guestbook note, `message` to write to me privately, and `stats` for the visit counter. The backend is a separate FastAPI service: [portfolio-api](https://github.com/Stars0-0/portfolio-api).
- **Skill matcher.** A small JavaScript version of my Python recommender: TF-IDF weights, cosine similarity, ranked roles. Runs on a made-up list of 7 roles.
- **KNN playground.** Click or drag a point and change k to see the vote. Even values of k can tie, and the nearest neighbour breaks the tie.
- **Accessibility.** axe-core reports no violations at 390 px and 1366 px wide. Every control works from the keyboard. Reduced-motion settings are respected. The content reads fine without JavaScript, though the terminal and demos need it.

## Run it

Open `index.html` in a browser.

## Files

- `index.html` is the whole site.
- `Kristan_Martinez_Resume.pdf` is the résumé the buttons link to.
