# Lux AI Challenge

This repository is a cleaned version of the official **LUX AI Challenge** kit that can be found here: Each programming language has a starter kit, you can find general API documentation here: https://github.com/Lux-AI-Challenge/Lux-Design-2021

## Getting Started

You will need Node.js version 12 or above. See installation instructions [here](https://nodejs.org/en/download/), you can just download the recommended version.


Open up the command line, and install the competition design with

```
npm install -g @lux-ai/2021-challenge@latest
```

You may ignore any warnings that show up, those are harmless. To run a match from the command line (CLI), simply run

## Your first BOT

Your BOT must be inserted as a subfolder inside the `bots` folder.
As a first try you must copy the _simple_ kit BOT you'll find in `kits/[lang]/simple` where `[lang]` is your desired language.

I prepared some bash scripts that can be used for Python bots, please make your modification for other languages

Inside the `bots` folder each bot has its own forder with the name of the Bot itself.

## Testing the BOT

Testing the Bot means trying your Bot against another one
To test the bot you need to run the `lux-ai-2021` engine with two bots (can be called with the same bot)

```
lux-ai-2021 path/to/botfile path/to/otherbotfile
```

I wrote a script shell that can be used to launch the test:

```sh
# run the BOT1 against the 'simple' bot of the kit
./run.sh BOT1

# run the BOT1 against BOT2
./run.sh BOT1 BOT2
```
Result of the test is a _json_ replay file you will find inside the `replays` folder.
You can watch the replay stored in the replays folder using our [visualizer](https://2021vis.lux-ai.org/).

To watch the replay locally, follow instructions here https://github.com/Lux-AI-Challenge/LuxViewer2021/

## Prepare for submition

To prepare the file for submition you can use the script :

```sh
./submit.sh BOT
```

this will create a `{BOT}.tar.gz` file inside the `submits` folder.

This file is ready to be submitted to the challenge on your [Lux AI Kaggle](https://www.kaggle.com/c/lux-ai-2021/submit) submit page.