# BGF-CONTRACT-GATE-FORMAT-BRITTLENESS-069

## Failure class

A construction gate can report a false regression when it compares a SQL contract using one exact formatting string. Newlines, indentation or spacing around commas may change while the database semantics remain identical.

Stage 15 exposed this when the 14-day BlackGold Trial row was correct in the migration and already applied remotely, but the CI gate searched for one minified tuple representation and failed.

## Permanent prevention

Semantic SQL contracts that span formatted statements must use whitespace-tolerant structural matching instead of one exact minified substring.

The subscription entitlement gate now validates the Trial tuple through a regex that accepts formatting changes while still fixing the required semantic values:

- plan code `trial`;
- display name `BlackGold Trial`;
- lifecycle `active`;
- 10 students;
- 1 member;
- 14 trial days.

## Regression contract

Formatting-only SQL edits must not fail a semantic contract gate. Real value drift must still fail closed with the domain-specific failure class (`BGF-SUBSCRIPTION-TRIAL-BOOTSTRAP-050`).
