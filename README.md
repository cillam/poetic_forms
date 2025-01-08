# Poetic Form Classification Using BERT-BiLSTM Architecture

## Project Overview
Poetic form classification presents an interesting challenge within the study of natural language processing due to the subjective and dynamic nature of poetry and poetic forms. In this project, I propose a hybrid architecture combining BERT with a BiLSTM layer to capture both contextual (i.e., themes and subject matter) and structural (i.e., stanza length or repetition and stress patterns) features of poetry.

## Results
The model was trained and evaluated on a dataset of 2,270 poems across nine poetic forms, demonstrating that the hybrid approach achieves an F1-weighted-average score of 0.86 (F1-macro: 0.83). Analysis of the results reveals that unfixed forms, such as odes and ballads, which rely on imagery and themes to shape form, were challenging for the model to distinguish. In contrast, the patterns of fixed forms, such as sonnets and villanelles, were more easily learned.

## Data Collection and Preparation
Data was combined from multiple sources:
- A dataset created by the authors of [*Sonnet or Not, Bot? Poetry Evaluation for Large Models and Datasets*](https://arxiv.org/abs/2406.18906) (1,453 poems, [GitHub Repository](https://github.com/maria-antoniak/poetry-eval/blob/main/data/poetry-evaluation_public-domain-poems.csv))
- A Kaggle dataset (6,300 poems, [Dataset Link](https://www.kaggle.com/datasets/michaelarman/poemsdataset))
- Poetry Foundation website scraping (2,387 poems)

## Data Cleaning Process
The data cleaning process involved:
- Removing non-English poems while keeping English translations
- Eliminating author notes and extraneous text
- Creating a standardized dataframe with metadata such as author, title, form, and topics

## Classification Scope
For the classification task, nine specific forms were focused on:
- Villanelle
- Sestina
- Pantoum
- Sonnet
- Ballad
- Blank verse
- Elegy
- Pastoral
- Ode

Irregular versions of the noted forms were excluded, resulting in a final filtered dataset of 2,270 poems. The dataset had a significant class imbalance, with sonnets being overrepresented. Rather than using undersampling, class weights were used to address the imbalance while preserving all poems and their potentially unique linguistic patterns.
