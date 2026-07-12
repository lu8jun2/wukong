# Wukong

Wukong 是一个面向 Codex 工作流的协调契约与公开技能包，不是 OpenAI 官方产品。  
Wukong is a coordinator contract and public Codex skill bundle, not an official OpenAI product.

## 它是什么 / What It Is

Wukong 把多代理协作约束成一套可验证的控制面：

- 协调者只负责对话、拆解、派工、状态、依赖和汇总
- 执行、研究、编码、测试、验证都必须落到有边界的 worker
- 项目必须先有 `project-control/v1` 控制文档
- 历史写回必须经过 historian handoff
- Chang'e 设计启动必须经过 Product Design gate

This bundle contains sanitized public skills, schemas, templates, examples, the full public role-reference tree, and local validation helpers for that contract.

## 架构 / Architecture

1. `AGENTS.md`: public coordinator baseline
2. `skills/multi-agent-wukong/`: coordinator contract, gates, schemas, templates
3. `skills/multi-agent-wukong/references/`: full role-reference tree, including `team-roles.md`, `agency-agent-role-map.md`, and `agency-agent-role-map.json`
4. `skills/codex-history/`: historian workflow and starter history script
5. `docs/`: install, security, cross-platform, and control-document templates
6. `examples/`: project-level AGENTS and config placeholders
7. `tests/`: path-neutral smoke and contract tests

## 安装 / Installation

### Windows

1. Clone or copy this bundle into a local folder.
2. Keep UTF-8 text handling enabled for Python-based validation.
3. Run:

```powershell
python -m unittest discover -s tests -v
python <plugin-creator-root>/scripts/validate_plugin.py .
```

4. Verify the full role-reference tree is present before use:

```powershell
Test-Path skills/multi-agent-wukong/references/team-roles.md
Test-Path skills/multi-agent-wukong/references/agency-agent-role-map.md
Test-Path skills/multi-agent-wukong/references/agency-agent-role-map.json
```

### macOS

See [docs/macOS-install.md](docs/macOS-install.md).

### Linux

Use the same flow as macOS with `python3` if your system maps that name to the active interpreter.

## 使用流 / Usage Flow

1. Bootstrap `<project-root>/docs/wukong/PROJECT-CONTROL.md` from the public template.
2. Confirm scope with the user.
3. Run `superpowers:brainstorming` for project-start and large tasks.
4. Before choosing or delegating a role, consult `skills/multi-agent-wukong/references/team-roles.md`; when an external specialist is relevant, also consult `agency-agent-role-map.md` and/or `agency-agent-role-map.json`.
5. Build a worker task packet with authorization, control-doc CAS, write scope, TDD state, external capability evaluation, and stop condition.
6. Execute through a worker.
7. Hand off to the historian.
8. Run independent verification before completion.

## 硬约束 / Hard Constraints

- Wukong is coordinator-only.
- No recursive dispatch by default.
- The full role-reference tree is required; abbreviated role docs or missing agency-role maps are invalid.
- No substantive work without a canonical project-control document.
- No completion claim without independent verification evidence.
- No design output from Chang'e before Product Design invocation evidence exists.

## Product Design Gate

`CHANG_E_PRODUCT_DESIGN_PLUGIN_GATE` is fail-closed. Public behavior is documented exactly as:

`BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE`

This bundle does not claim live Product Design runtime availability. Metadata or capability selection alone does not unlock downstream design.

## 安全排除项 / Security Exclusions

The public bundle excludes:

- auth tokens, cookies, secrets, local machine state
- task history dumps and local evidence databases
- plugin caches, backups, and private outputs
- live `config.toml`, live control documents, and private project artifacts
- absolute local paths, usernames, private URLs, and machine-specific hashes

## Project-Control Requirement

Use [docs/PROJECT-CONTROL.template.md](docs/PROJECT-CONTROL.template.md) as the public starting point. The live private governance control document is not included.

## Goal Policy

The public baseline keeps Goal status at `NOT_CREATED_BY_USER_DIRECTION`.  
Project-specific Goals are future work and require explicit user confirmation plus compile, tests, and review gates.

## 验证 / Verification

Run the public bundle checks locally:

```bash
python -m unittest discover -s tests -v
python scripts/redaction_scan.py --root . --out release-evidence/redaction-scan.json
python scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
python scripts/build_manifest.py --root . --out release-evidence/MANIFEST.json
```

Role-reference tree verification is part of the public contract. A valid bundle includes:

- `skills/multi-agent-wukong/references/team-roles.md`
- `skills/multi-agent-wukong/references/agency-agent-role-map.md`
- `skills/multi-agent-wukong/references/agency-agent-role-map.json`

## 贡献 / Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep public changes path-neutral, secret-free, and independently verifiable.

## 限制 / Limitations

- This bundle documents a coordination contract; it does not ship a live agent runtime.
- Product Design runtime invocation stays blocked unless a real runtime and evidence are present.
- Independent verification is a required separate responsibility, not a suggestion.
