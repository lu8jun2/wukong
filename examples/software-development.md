# Example: software development

This example shows a safe feature task after installation. `Role=Wukong/悟空` receives the user request, confirms scope, and dispatches the implementation worker; Wukong does not edit or test the code itself.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Before dispatch, Wukong displays the control record:

```text
Role=Wukong/悟空
PROJECT-CONTROL path: <project-root>/docs/wukong/PROJECT-CONTROL.md
schema: project-control/v1
revision: r1
sha256: <64 lowercase hex>
status: VALID
Delegation permission: FORBIDDEN
independent verifier: required
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Safe dialogue test:

```text
Role=Wukong/悟空，请为“添加输入校验”创建一个待确认任务包；只说明范围、测试计划、
控制文档 path/schema/revision/sha256/status，不要直接修改文件，也不要递归派发。
```

The implementation worker returns its handoff to `Role=Public Historian/公共史官`; an independent verifier then checks the diff and tests before Wukong reports completion.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.
