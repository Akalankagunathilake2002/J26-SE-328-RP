<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: GitHub Actions CI/CD -->
<!-- source: GitHub Docs -->
<!-- license: CC BY 4.0 -->
<!-- url: https://docs.github.com/en/actions/concepts/workflows-and-actions/expressions -->
# Expressions

You can evaluate expressions in workflows and actions.

## About expressions

You can use expressions to programmatically set environment variables in workflow files and access contexts. An expression can be any combination of literal values, references to a context, or functions. You can combine literals, context references, and functions using operators. For more information about contexts, see AUTOTITLE.

Expressions are commonly used with the conditional `if` keyword in a workflow file to determine whether a step should run. When an `if` conditional is `true`, the step will run.

`$`

> [!NOTE]
> The exception to this rule is when you are using expressions in an `if` clause, where, optionally, you can usually omit `$`. For more information about `if` conditionals, see AUTOTITLE.

### Example setting an environment variable

```yaml
env:
  MY_ENV_VAR: $
```

## Further reading

For technical reference information about expressions you can use in workflows and actions, see AUTOTITLE.
