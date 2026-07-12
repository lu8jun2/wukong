# Agency Agents -> Wukong Role Map

This file maps every installed Agency Agents definition in the public role-reference tree to a Wukong permanent role. Rebuild it from the local source of truth with:

```powershell
python -X utf8 <skill-root>\scripts\generate_agency_agent_role_map.py
```

## Routing Rules

- Wukong remains the coordinator. Agency Agents are external specialists used by the mapped role.
- The primary role owns dispatch, context, and result validation for that external agent.
- Secondary roles review cross-cutting concerns but do not override the primary owner without Wukong arbitration.
- If a new agent is installed, regenerate this map and rerun the Wukong tests.

## Role Counts

| Wukong role | Agent count |
|---|---:|
| 二郎神 | 33 |
| 哪吒 | 22 |
| 唐僧 | 11 |
| 太上老君 | 33 |
| 嫦娥 | 72 |
| 沙僧 | 14 |
| 猪八戒 | 6 |
| 白龙马 | 9 |
| 观音 | 43 |

## Full Map

| Agent id | Agent name | Primary role | Secondary roles | Capability cluster |
|---|---|---|---|---|
| `3d-scene-developer` | 3D & Scene Developer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `accessibility-auditor` | Accessibility Auditor | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `account-strategist` | Account Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `accounts-payable-agent` | Accounts Payable Agent | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `ad-creative-strategist` | Ad Creative Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `aeo-foundations-architect` | AEO Foundations Architect | 唐僧 | 沙僧 | 架构与边界 |
| `agentic-identity-trust-architect` | Agentic Identity & Trust Architect | 唐僧 | 沙僧 | 架构与边界 |
| `agentic-search-optimizer` | Agentic Search Optimizer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `agents-orchestrator` | Agents Orchestrator | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `ai-citation-strategist` | AI Citation Strategist | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `ai-data-remediation-engineer` | AI Data Remediation Engineer | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `ai-engineer` | AI Engineer | 猪八戒 | 唐僧 / 沙僧 | 核心开发 |
| `analytics-reporter` | Analytics Reporter | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `anthropologist` | Anthropologist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `api-tester` | API Tester | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `app-store-optimizer` | App Store Optimizer | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `application-security-engineer` | Application Security Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `automation-governance-architect` | Automation Governance Architect | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `autonomous-optimization-architect` | Autonomous Optimization Architect | 唐僧 | 沙僧 | 架构与边界 |
| `backend-architect` | Backend Architect | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `baidu-seo-specialist` | Baidu SEO Specialist | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `behavioral-nudge-engine` | Behavioral Nudge Engine | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `bilibili-content-strategist` | Bilibili Content Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `bim-gis-specialist` | BIM/GIS Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `blender-add-on-engineer` | Blender Add-on Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `blockchain-security-auditor` | Blockchain Security Auditor | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `book-co-author` | Book Co-Author | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `bookkeeper-controller` | Bookkeeper & Controller | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `brand-guardian` | Brand Guardian | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `business-strategist` | Business Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `carousel-growth-engine` | Carousel Growth Engine | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `cartography-designer` | Cartography Designer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `change-management-consultant` | Change Management Consultant | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `chief-financial-officer` | Chief Financial Officer | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `chief-of-staff` | Chief of Staff | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `china-e-commerce-operator` | China E-Commerce Operator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `china-market-localization-strategist` | China Market Localization Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `civil-engineer` | Civil Engineer | 猪八戒 | 唐僧 / 沙僧 | 核心开发 |
| `clinical-evidence-agent` |        Clinical Evidence Agent | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `cloud-security-architect` | Cloud Security Architect | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `cms-developer` | CMS Developer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `code-reviewer` | Code Reviewer | 唐僧 | 沙僧 | 架构与边界 |
| `codebase-onboarding-engineer` | Codebase Onboarding Engineer | 唐僧 | 沙僧 | 架构与边界 |
| `compliance-auditor` | Compliance Auditor | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `content-creator` | Content Creator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `corporate-training-designer` | Corporate Training Designer | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `cross-border-e-commerce-specialist` | Cross-Border E-Commerce Specialist | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `cultural-intelligence-strategist` | Cultural Intelligence Strategist | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `customer-service` | Customer Service | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `customer-success-manager` | Customer Success Manager | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `data-consolidation-agent` | Data Consolidation Agent | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `data-engineer` | Data Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `data-privacy-officer` | Data Privacy Officer | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `database-optimizer` | Database Optimizer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `deal-strategist` | Deal Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `developer-advocate` | Developer Advocate | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `devops-automator` | DevOps Automator | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `discovery-coach` | Discovery Coach | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `document-generator` | Document Generator | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `douyin-strategist` | Douyin Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `drone-reality-mapping-specialist` | Drone/Reality Mapping Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `drupal-performance-engineer` | Drupal Performance Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `drupal-shopping-cart-engineer` | Drupal Shopping Cart Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `email-intelligence-engineer` | Email Intelligence Engineer | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `email-marketing-strategist` | Email Marketing Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `embedded-firmware-engineer` | Embedded Firmware Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `esg-sustainability-officer` | ESG & Sustainability Officer | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `evidence-collector` | Evidence Collector | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `executive-summary-generator` | Executive Summary Generator | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `experiment-tracker` | Experiment Tracker | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `fedramp-rmf-compliance-engineer` | FedRAMP & RMF Compliance Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `feedback-synthesizer` | Feedback Synthesizer | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `feishu-integration-developer` | Feishu Integration Developer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `filament-optimization-specialist` | Filament Optimization Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `finance-tracker` | Finance Tracker | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `financial-analyst` | Financial Analyst | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `fp-a-analyst` | FP&A Analyst | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `french-consulting-market-navigator` | French Consulting Market Navigator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `frontend-developer` | Frontend Developer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `game-audio-engineer` | Game Audio Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `game-designer` | Game Designer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `geoai-ml-engineer` | GeoAI/ML Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `geographer` | Geographer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `geoprocessing-specialist` | Geoprocessing Specialist | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `gis-analyst` | GIS Analyst | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `gis-qa-engineer` | GIS QA Engineer | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `git-workflow-master` | Git Workflow Master | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `global-podcast-strategist` | Global Podcast Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `godot-gameplay-scripter` | Godot Gameplay Scripter | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `godot-multiplayer-engineer` | Godot Multiplayer Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `godot-shader-developer` | Godot Shader Developer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `government-digital-presales-consultant` | Government Digital Presales Consultant | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `grant-writer` | Grant Writer | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `growth-hacker` | Growth Hacker | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `healthcare-customer-service` | Healthcare Customer Service | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `healthcare-marketing-compliance-specialist` | Healthcare Marketing Compliance Specialist | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `historian` | Historian | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `hospitality-guest-services` | Hospitality Guest Services | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `hr-onboarding` | HR Onboarding | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `identity-graph-operator` | Identity Graph Operator | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `image-prompt-engineer` | Image Prompt Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `incident-responder` | Incident Responder | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `incident-response-commander` | Incident Response Commander | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `inclusive-visuals-specialist` | Inclusive Visuals Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `infrastructure-maintainer` | Infrastructure Maintainer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `instagram-curator` | Instagram Curator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `internationalization-engineer` | Internationalization Engineer | 猪八戒 | 唐僧 / 沙僧 | 核心开发 |
| `investment-researcher` | Investment Researcher | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `it-service-manager` | IT Service Manager | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `jira-workflow-steward` | Jira Workflow Steward | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `korean-business-navigator` | Korean Business Navigator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `kuaishou-strategist` | Kuaishou Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `language-translator` | Language Translator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `legal-billing-time-tracking` | Legal Billing & Time Tracking | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `legal-client-intake` | Legal Client Intake | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `legal-compliance-checker` | Legal Compliance Checker | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `legal-document-review` | Legal Document Review | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `level-designer` | Level Designer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `linkedin-content-creator` | LinkedIn Content Creator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `livestream-commerce-coach` | Livestream Commerce Coach | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `loan-officer-assistant` | Loan Officer Assistant | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `lsp-index-engineer` | LSP/Index Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `m-a-integration-manager` | M&A Integration Manager | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `macos-spatial-metal-engineer` | macOS Spatial/Metal Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `mcp-builder` | MCP Builder | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `medical-billing-coding-specialist` | Medical Billing & Coding Specialist | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `meeting-notes-specialist` | Meeting Notes Specialist | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `minimal-change-engineer` | Minimal Change Engineer | 唐僧 | 沙僧 | 架构与边界 |
| `mobile-app-builder` | Mobile App Builder | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `model-qa-specialist` | Model QA Specialist | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `multi-agent-systems-architect` | Multi-Agent Systems Architect | 唐僧 | 沙僧 | 架构与边界 |
| `multi-platform-publisher` | Multi-Platform Publisher | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `narrative-designer` | Narrative Designer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `narratologist` | Narratologist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `network-engineer` | Network Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `offer-lead-gen-strategist` | Offer & Lead Gen Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `operations-manager` | Operations Manager | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `organizational-psychologist` | Organizational Psychologist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `orgscript-engineer` | OrgScript Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `outbound-strategist` | Outbound Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `paid-media-auditor` | Paid Media Auditor | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `paid-social-strategist` | Paid Social Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `payments-billing-engineer` | Payments & Billing Engineer | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `penetration-tester` | Penetration Tester | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `performance-benchmarker` | Performance Benchmarker | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `persona-walkthrough-specialist` | Persona Walkthrough Specialist | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `personal-growth-mentor` | Personal Growth Mentor | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `pipeline-analyst` | Pipeline Analyst | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `podcast-strategist` | Podcast Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `ppc-campaign-strategist` | PPC Campaign Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `pr-communications-manager` | PR & Communications Manager | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `pricing-analyst` | Pricing Analyst | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `private-domain-operator` | Private Domain Operator | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `product-manager` | Product Manager | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `programmatic-display-buyer` | Programmatic & Display Buyer | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `project-shepherd` | Project Shepherd | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `prompt-engineer` | Prompt Engineer | 猪八戒 | 唐僧 / 沙僧 | 核心开发 |
| `proposal-strategist` | Proposal Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `psychologist` | Psychologist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `rapid-prototyper` | Rapid Prototyper | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `real-estate-buyer-seller` | Real Estate Buyer & Seller | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `reality-checker` | Reality Checker | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `recruitment-specialist` | Recruitment Specialist | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `reddit-community-builder` | Reddit Community Builder | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `report-distribution-agent` | Report Distribution Agent | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `retail-customer-returns` | Retail Customer Returns | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `roblox-avatar-creator` | Roblox Avatar Creator | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `roblox-experience-designer` | Roblox Experience Designer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `roblox-systems-scripter` | Roblox Systems Scripter | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `sales-coach` | Sales Coach | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `sales-data-extraction-agent` | Sales Data Extraction Agent | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `sales-engineer` | Sales Engineer | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `sales-outreach` | Sales Outreach | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `salesforce-architect` | Salesforce Architect | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `search-query-analyst` | Search Query Analyst | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `section-508-accessibility-specialist` | Section 508 Accessibility Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `security-architect` | Security Architect | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `senior-developer` | Senior Developer | 唐僧 | 沙僧 | 架构与边界 |
| `senior-project-manager` | Senior Project Manager | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `senior-secops-engineer` | Senior SecOps Engineer | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `seo-specialist` | SEO Specialist | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `short-video-editing-coach` | Short-Video Editing Coach | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `social-media-strategist` | Social Media Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `software-architect` | Software Architect | 唐僧 | 沙僧 | 架构与边界 |
| `solidity-smart-contract-engineer` | Solidity Smart Contract Engineer | 猪八戒 | 唐僧 / 沙僧 | 核心开发 |
| `solution-engineer` | Solution Engineer | 唐僧 | 沙僧 | 架构与边界 |
| `sovereign-health-systems-agent` |        Sovereign Health Systems Agent | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `spatial-data-engineer` | Spatial Data Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `spatial-data-scientist` | Spatial Data Scientist | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `sprint-prioritizer` | Sprint Prioritizer | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `sre-site-reliability-engineer` | SRE (Site Reliability Engineer) | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `strategy-duel-agent` | Strategy Duel Agent | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `studio-operations` | Studio Operations | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `studio-producer` | Studio Producer | 白龙马 | 悟空 / 沙僧 | 稳定执行 |
| `study-abroad-advisor` | Study Abroad Advisor | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `supply-chain-strategist` | Supply Chain Strategist | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `support-responder` | Support Responder | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `tax-strategist` | Tax Strategist | 哪吒 | 观音 / 沙僧 | 经营合规与组织 |
| `technical-artist` | Technical Artist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `technical-consultant` | Technical Consultant | 唐僧 | 沙僧 | 架构与边界 |
| `technical-writer` | Technical Writer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `terminal-integration-specialist` | Terminal Integration Specialist | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `test-automation-engineer` | Test Automation Engineer | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `test-results-analyzer` | Test Results Analyzer | 沙僧 | 猪八戒 / 二郎神 | 验证与恢复 |
| `threat-detection-engineer` | Threat Detection Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `threat-intelligence-analyst` | Threat Intelligence Analyst | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `tiktok-strategist` | TikTok Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `tool-evaluator` | Tool Evaluator | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `tracking-measurement-specialist` | Tracking & Measurement Specialist | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `trend-researcher` | Trend Researcher | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `twitter-engager` | Twitter Engager | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `ui-designer` | UI Designer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unity-architect` | Unity Architect | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unity-editor-tool-developer` | Unity Editor Tool Developer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unity-multiplayer-engineer` | Unity Multiplayer Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unity-shader-graph-artist` | Unity Shader Graph Artist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unreal-multiplayer-architect` | Unreal Multiplayer Architect | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unreal-systems-engineer` | Unreal Systems Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unreal-technical-artist` | Unreal Technical Artist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `unreal-world-builder` | Unreal World Builder | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `uswds-developer` | USWDS Developer | 猪八戒 | 唐僧 / 沙僧 | 核心开发 |
| `ux-architect` | UX Architect | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `ux-researcher` | UX Researcher | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `video-optimization-specialist` | Video Optimization Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `visionos-spatial-engineer` | visionOS Spatial Engineer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `visual-storyteller` | Visual Storyteller | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `voice-ai-integration-engineer` | Voice AI Integration Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `web-gis-developer` | Web GIS Developer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `wechat-mini-program-developer` | WeChat Mini Program Developer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `wechat-official-account-manager` | WeChat Official Account Manager | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `weibo-strategist` | Weibo Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `whimsy-injector` | Whimsy Injector | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `wordpress-performance-engineer` | WordPress Performance Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `wordpress-shopping-cart-engineer` | WordPress Shopping Cart Engineer | 二郎神 | 唐僧 / 沙僧 | 平台与后端 |
| `workflow-architect` | Workflow Architect | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `workflow-optimizer` | Workflow Optimizer | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `x-twitter-intelligence-analyst` | X/Twitter Intelligence Analyst | 太上老君 | 观音 / 沙僧 | 长研究与流程 |
| `xiaohongshu-specialist` | Xiaohongshu Specialist | 观音 | 太上老君 / 沙僧 | 业务与内容 |
| `xr-cockpit-interaction-specialist` | XR Cockpit Interaction Specialist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `xr-immersive-developer` | XR Immersive Developer | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `xr-interface-architect` | XR Interface Architect | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `zhihu-strategist` | Zhihu Strategist | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
| `zk-steward` | ZK Steward | 嫦娥 | 观音 / 沙僧 | 体验与视觉 |
