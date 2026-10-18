<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#step-functions-tips -->
# AWS Guide: Step Functions Tips

-   A variety of structures are supported including branching, parallel operations and waits
-   Tasks represent the real work nodes and are frequently Lambda functions, but can be Activities which are externally driven tasks implemented any way you like.
-   State machines have data that "flows" through the steps and can be modified and added to as the state machine executes.
-   It's best if your tasks are idempotent, in part because you may want to re-run the state machine with the same input data during debugging
-   The AWS Console facilitates your examining the execution state at various steps.
    -   The console lets you do this with a few steps:
        -   select the "input" tab from the failed execution
        -   copy the input data (JSON)
        -   select the state machine name in the breadcrumbs
        -   start a new execution, pasting the input data you copied previously

Back to top :arrow_up:
