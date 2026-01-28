# Activism Dictionary (Italian)

## Purpose

This dictionary is designed to **filter parliamentary speeches that mention activism-related phenomena**. It is intentionally **recall-oriented** (inclusive) and is used **only to delimit the analytic corpus**. It is *not* a framing or sentiment instrument.

## Conceptual Definition

In line with social movement theory and the semiotics of protest, *activism* is defined as **non-institutional or extra-parliamentary collective action** aimed at expressing dissent, advancing claims, or mobilising support around social, political, or economic issues.

This definition follows classic distinctions between institutional political activity and collective action occurring outside formal representative channels.

## Scope and Annotation Level

* **Unit of filtering:** whole speech
* **Matching level:** surface-form (case-insensitive)
* **Decision rule:** a speech is retained if it contains *at least one* dictionary term

False positives are tolerated at this stage; false negatives are minimised.

## Theoretical Rationale

The dictionary is theory-driven and grounded in:

* Social movement theory (e.g. mobilisation, collective action, protest)
* Italian-language scholarship on protest and activism
* Semiotic distinctions between forms of dissent (e.g. protest vs. revolt)

Terms are selected based on **semantic proximity** to the core concept of activism rather than frequency alone.

## Semantic Domains

### 1. Protest and Dissent

Terms referring to public expression of opposition or disagreement.

* protesta
* proteste
* protestare
* dissenso
* contestazione
* contestare
* opposizione sociale

### 2. Collective Action and Mobilisation

Terms describing organised or collective participation.

* mobilitazione
* mobilitazioni
* mobilitare
* azione collettiva
* partecipazione collettiva
* attivazione

### 3. Movements and Activism

Terms explicitly naming activism or social movements.

* attivismo
* attivista
* attivisti
* movimento
* movimenti
* movimento sociale
* movimenti sociali
* movimento politico
* movimenti politici

### 4. Demonstrations and Public Gatherings

Terms denoting public events of protest.

* manifestazione
* manifestazioni
* corteo
* cortei
* presidio
* sit-in
* sciopero
* scioperi

### 5. Claim-Making and Grievances

Terms related to demands and collective claims.

* rivendicazione
* rivendicazioni
* richiesta collettiva
* istanza sociale

## Boundary Terms (Monitored Separately)

The following terms refer to more radical or violent forms of contention. They are **included for recall** but flagged for later inspection.

* rivolta
* rivolte
* sommossa
* insurrezione

## Excluded Terms

The following are *not* included because they refer primarily to institutional politics or individual opinion:

* dibattito parlamentare
* mozione
* emendamento
* interrogazione
* opinione personale

## Implementation Notes

* Matching is case-insensitive
* No lemmatisation is applied at this stage
* Plural and gender variants are explicitly included where relevant

## Validation Plan

* Manual inspection of a random sample of retained speeches
* Manual inspection of a random sample of excluded speeches
* Iterative refinement of terms based on observed false negatives

## Versioning

* v1.0: Initial theory-driven seed dictionary (pre-spaCy)

---

This dictionary constitutes a transparent and replicable first filtering step prior to segment-level annotation, linguistic preprocessing, sentiment analysis, and framing analysis.