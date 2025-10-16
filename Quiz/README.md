graph TD
    A[User] --> B(User Interaction Agent);
    B --> C(Knowledge Checker Agent);
    C -- "Ask for Target Cert & Scope" --> D{Get Required Context};
    D --> C;
    C -- "Invoke Lambda: GenerateQuestionSet" --> E(Lambda: GenerateQuestionSet);
    E -- "Read from CertificationSyllabus" --> F[DynamoDB: CertificationSyllabus];
    E -- "Query for questions" --> G[Vector Store];
    G --> E -- "Questions with rationale" --> C;
    C -- "Provide 1 question at a time" --> H[User Answers];
    H --> I(Agent provides feedback);
    I -- "After each Q" --> J(Lambda: UpdateUserKnowledgeProfile);
    J -- "Update scores & weak areas" --> K[DynamoDB: UserKnowledgeProfile];
    K --> J;
    C -- "End of quiz" --> L(Agent provides overall feedback);
