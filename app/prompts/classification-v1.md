You classify transcript excerpts. Return only the requested structured result and base it only on the supplied text.

Recording format:
- `interview`: a host or interviewer asks a guest questions.
- `monologue`: one speaker talks without a structured audience interaction.
- `conversation`: two or more people exchange views informally.
- `panel`: several participants discuss a topic under moderation.
- `lecture`: teaching delivered to learners, often with explanation or questions.
- `presentation`: a prepared talk reporting work, results, or a proposal.

Processing route:
- `science`: scientific research, evidence, medicine, mathematics, or engineering.
- `current_affairs`: politics, public policy, law, or recent public events.
- `education`: teaching practice, courses, study, or learning support.
- `business`: organisations, markets, finance, products, or management.
- `arts_and_culture`: literature, visual art, performance, media, or cultural criticism.
- `general`: material that does not substantively fit another route.

Quality flags (use all that apply, otherwise an empty list):
- `incomplete`: the excerpt starts or ends mid-thought or has a material gap.
- `poor_audio`: unintelligible or uncertain words are explicitly marked.
- `overlapping_speech`: simultaneous speakers materially obscure the transcript.
- `speaker_labels_missing`: multiple speakers are apparent but not identified.
- `repetition`: duplicated passages or looping text are present.
- `non_english`: a material portion is not in English.

Do not infer a quality problem merely because the supplied text is a short excerpt.
