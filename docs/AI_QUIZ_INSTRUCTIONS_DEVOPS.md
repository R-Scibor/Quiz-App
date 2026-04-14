# AI Quiz Generation Instructions — DevOps (Kubernetes / kubectl / YAML)

Read and follow the **Generic Instructions** (`AI_QUIZ_INSTRUCTIONS_GENERIC.md`) first. This document extends and overrides it for DevOps topics.

---

## Scope & Focus

Generate quizzes from Kubernetes and DevOps source material. Match the question mix to the source — if the source is mostly conceptual, produce mostly theory questions; if it's a CLI reference, produce mostly `open-cli`. The four pillars are equally important:

1. **Theory & concepts** — how resources work, when to use which type, what happens internally. Always present regardless of source type.
2. **kubectl commands** — practical command recall and construction. Include when the source covers CLI usage.
3. **YAML manifests** — reading, writing, and debugging Kubernetes resource definitions. Include when the source covers resource specs.
4. **Operational debugging** — how to diagnose and fix real cluster problems. Include when the source covers troubleshooting.

---

## Question Type Usage for DevOps

### `single-choice` / `multiple-choice` — For theory, facts, and comparisons
These are the backbone of any topic. Use liberally for:
- Definitions and what a resource/field does
- Default values and behaviors (default Service type, default `imagePullPolicy`, etc.)
- Which resource/type to use in a given scenario
- Comparisons between similar concepts (ClusterIP vs NodePort, liveness vs readiness probe)
- What a specific flag or field means
- Port ranges, naming conventions, API group values

**Every topic should have at least 2–3 closed questions**, even if it also has open-type questions.

### `open-text` — For explanations and reasoning
Use for: explaining what a resource does in your own words, why a design decision exists, the difference between two concepts when nuance matters, what happens internally when X occurs.

### `open-cli` — For kubectl commands
Use for any question whose answer is a kubectl command or shell command sequence. Include when the source material covers CLI usage.

**Write `open-cli` questions for:**
- Retrieving resource info (`kubectl get`, `kubectl describe`, `kubectl logs`)
- Creating/applying resources (`kubectl apply`, `kubectl create`, `kubectl run`, `kubectl expose`)
- Modifying resources (`kubectl scale`, `kubectl set`, `kubectl label`, `kubectl annotate`)
- Debugging (`kubectl exec`, `kubectl port-forward`, `kubectl debug`)
- Dry-run / output generation (`--dry-run=client -o yaml`)
- Namespace-specific operations (`-n`, `--namespace`, `--all-namespaces`, `-A`)
- Context/cluster management (`kubectl config`, `kubectl use-context`)

### `open-code` — For YAML authoring
Use for: "write the YAML manifest for...", "write a patch that...", "complete this manifest". Set `gradingCriteria` with `yaml:` prefix.

### `open-code` — For YAML authoring
Use for: "write the YAML manifest for...", "write a patch that...", "complete this manifest". Set `gradingCriteria` with `yaml:` prefix.

```json
{
  "type": "open-code",
  "gradingCriteria": "yaml: a Service manifest of type NodePort that targets port 8080 on Pods with label app=frontend, exposed on port 80, with nodePort 30080",
  "maxPoints": 4
}
```

---

## kubectl Regex Patterns — Reference and Rules

### Core regex rules

```
\\s+          — one or more whitespace characters (between tokens)
(a|b)         — alternatives (short flag vs long flag, aliases)
(\\s+...)?    — optional group (e.g. namespace flag is often optional)
(-n\\s+|-n=)  — namespace short flag variants
(--namespace(=|\\s+))  — namespace long flag
```

### Namespace flag pattern (reusable)
Most kubectl commands accept namespace as either short or long form:
```
(-n\\s+|--namespace(=|\\s+))NAMESPACE
```
For questions where namespace is optional (global or already-scoped):
```
(\\s+(-n\\s+|--namespace(=|\\s+))NAMESPACE)?
```
To accept both specific namespace AND `--all-namespaces`/`-A`:
```
(\\s+(-n\\s+|--namespace(=|\\s+))NAMESPACE|\\s+(--all-namespaces|-A))?
```

### Output format flag pattern
```
(\\s+(-o\\s+|--output(=|\\s+))(yaml|json|wide|name))?
```

### Common kubectl regex templates

**Get pods (any namespace variant):**
```
kubectl\\s+(get)\\s+(pods|po)(\\s+(-n\\s+|--namespace(=|\\s+))\\S+|\\s+(--all-namespaces|-A))?
```

**Get pods with label selector:**
```
kubectl\\s+get\\s+(pods|po)\\s+(-l\\s+|--selector(=|\\s+))app=myapp(\\s+(-n\\s+|--namespace(=|\\s+))\\S+)?
```

**Apply a file:**
```
kubectl\\s+apply\\s+(-f\\s+|--filename(=|\\s+))\\S+
```

**Dry-run to YAML:**
```
kubectl\\s+.*--dry-run(=client)?\\s+.*(-o\\s+|--output(=|\\s+))yaml|kubectl\\s+.*(-o\\s+|--output(=|\\s+))yaml\\s+.*--dry-run(=client)?
```

**Exec into a pod:**
```
kubectl\\s+exec\\s+(-it|-ti)\\s+\\S+(\\s+(-n\\s+|--namespace(=|\\s+))\\S+)?\\s+--\\s+.+
```

**Scale deployment:**
```
kubectl\\s+scale\\s+(deployment|deploy)(s)?\\s+\\S+\\s+--replicas(=|\\s+)\\d+
```

**Describe resource:**
```
kubectl\\s+describe\\s+(pod|pods|po|service|svc|deployment|deploy|node|nodes)\\s+\\S+(\\s+(-n\\s+|--namespace(=|\\s+))\\S+)?
```

**Logs:**
```
kubectl\\s+logs\\s+\\S+(\\s+(-n\\s+|--namespace(=|\\s+))\\S+)?(\\s+(-f|--follow))?(\\s+(-c\\s+|--container(=|\\s+))\\S+)?
```

### Regex quality rules
- Accept **both short and long forms** of flags: `-n` and `--namespace`, `-f` and `--filename`, `-o` and `--output`.
- Accept **both `=` and space** as separator for flags: `--namespace=prod` and `--namespace prod`.
- Accept **resource aliases**: `pods`/`po`, `services`/`svc`, `deployments`/`deploy`, `nodes`/`no`, `configmaps`/`cm`, `namespaces`/`ns`.
- For `maxPoints: 1` questions, design the regex to be the primary grader — keep it comprehensive enough that Gemini escalation is rare.
- For multi-step commands (pipes, `&&`), use `open-text` instead — regex cannot reliably validate pipelines.

---

## YAML Question Guidelines

### Embed YAML in questionText for reading/analysis questions
Always show the manifest when asking about it. Use the yaml code fence:

```json
"questionText": "What will happen when this Service is applied?\n\n```yaml\napiVersion: v1\nkind: Service\nmetadata:\n  name: my-service\nspec:\n  type: ClusterIP\n  selector:\n    app: backend\n  ports:\n    - port: 80\n      targetPort: 8080\n```"
```

### YAML field targeting
Write questions that target specific YAML fields that are commonly confused or misunderstood:
- `port` vs `targetPort` vs `nodePort` in Services
- `containerPort` (informational) vs Service `targetPort` (functional)
- `selector` in Service vs `selector` in Deployment (matchLabels)
- `replicas` vs HPA `minReplicas`/`maxReplicas`
- `imagePullPolicy: Always` vs `IfNotPresent` vs `Never`
- `resources.requests` vs `resources.limits`
- `livenessProbe` vs `readinessProbe` vs `startupProbe`

### "What's wrong with this YAML" questions
These are high-value analysis questions. Show a broken manifest with a subtle error and ask for diagnosis:
- Wrong indentation level for a field
- `selector` in Service that doesn't match Pod labels
- Missing required field (`spec.containers` without `name`)
- Wrong value type (string instead of integer)

Example question pattern:
```json
{
  "questionText": "This Service has a bug that prevents it from routing traffic to any Pod. What is wrong?\n\n```yaml\napiVersion: v1\nkind: Service\nmetadata:\n  name: web-svc\nspec:\n  selector:\n    app: web-frontend\n  ports:\n    - port: 80\n      targetPort: 8080\n```\n\nThe Pods have the label `app: frontend` (not `app: web-frontend`).",
  "type": "open-text",
  "gradingCriteria": "The Service selector 'app: web-frontend' does not match the Pod label 'app: frontend'. Because no Pods match the selector, the Endpoints object will be empty and traffic will not reach any Pod. Fix: change selector to 'app: frontend' or relabel the Pods.",
  "maxPoints": 2
}
```

---

## Kubernetes Concept Question Patterns

### "When to use which" scenario questions
These are high-value `single-choice` questions. Give a concrete scenario and ask which resource/type/approach fits best:

- "You need to expose a web app to users on the internet in a cloud cluster. Which Service type should you use?"
- "You have 5 HTTP microservices and want to route them through a single IP with path-based routing. What should you use?"
- "A StatefulSet pod needs to be individually addressable by DNS. What Service configuration enables this?"

### Cause-and-effect questions
Test understanding of Kubernetes internals:

- "A Pod's readiness probe starts failing. What immediately happens to the Service's Endpoints?"
- "You delete a Deployment. What happens to the Pods it managed?"
- "You increase a Deployment's `replicas` from 2 to 5. What rollout strategy does Kubernetes use by default?"

### Comparison questions (single-choice or open-text)
Test the ability to distinguish similar concepts:

- ClusterIP vs NodePort vs LoadBalancer
- `kubectl apply` vs `kubectl create`
- `livenessProbe` vs `readinessProbe`
- `ConfigMap` vs `Secret`
- Deployment vs StatefulSet vs DaemonSet

---

## DevOps Tag Strategy

Use these standard tag categories consistently:

**Resource type tags:** `pod`, `deployment`, `service`, `configmap`, `secret`, `ingress`, `statefulset`, `daemonset`, `job`, `cronjob`, `namespace`, `node`, `pv`, `pvc`, `serviceaccount`, `rbac`, `networkpolicy`

**Topic tags:** `kubectl`, `yaml`, `dns`, `networking`, `storage`, `scheduling`, `rbac`, `security`, `scaling`, `rolling-update`, `resource-limits`, `probes`, `labels-selectors`, `debugging`

**Skill tags:** `command`, `definition`, `comparison`, `debugging`, `config-authoring`, `scenario`, `analysis`

**Domain tags:** `kubernetes`, `docker`, `helm`, `ci-cd`, `linux`, `git`

Example:
```json
"tags": ["kubernetes", "service", "clusterip", "comparison", "scenario"]
```

---

## Mandatory Questions for Every Kubernetes Topic

When the source covers a Kubernetes resource or feature, always include at least:

1. **Two `single-choice` or `multiple-choice`** — One definition/fact question and one scenario or comparison question.
2. **One `open-text`** — "What does this resource do and when do you use it?" or an explanation of its internal behavior.
3. **One `open-cli`** — "Write the command to list/get/create/describe this resource." *(only if the source mentions CLI usage)*
4. **One YAML question** — Either show-and-explain (`single-choice`) or write-a-manifest (`open-code`). *(only if the source shows YAML)*

If the source is purely conceptual (no CLI or YAML content), replace items 3 and 4 with additional `open-text` and `single-choice` questions that go deeper on the theory.

---

## Debugging / Troubleshooting Questions

For any topic that involves debugging (connectivity, DNS, probe failures, etc.), write at least one question that mirrors a real on-call workflow:

**Pattern:** Give a symptom, ask for the diagnostic command sequence or root cause.

```json
{
  "questionText": "You apply a Service but `kubectl get endpoints my-service` shows `<none>`. What is the most likely cause and how do you verify it?",
  "type": "open-text",
  "gradingCriteria": "The Service selector does not match any Pod labels. Verify by running 'kubectl describe service my-service' to see the selector, then 'kubectl get pods --show-labels' to compare Pod labels. If selectors don't match, the Endpoints object will remain empty.",
  "maxPoints": 3,
  "tags": ["kubernetes", "service", "debugging", "endpoints", "selector"]
}
```

---

## Anti-Patterns to Avoid

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| Asking for exact port numbers that aren't practically memorable | Tests trivia, not skill | Test the concept (NodePort range exists, valid: 30000–32767), not the exact number unless critical |
| "`kubectl get pods -n kube-system`" with regex that only accepts one namespace flag form | Rejects valid answers | Accept `-n`, `--namespace=`, `--namespace ` all |
| `open-text` question with `gradingCriteria` that just restates the question | Grader has no rubric | Describe what a correct answer must contain |
| 10 `single-choice` questions all asking "what does X stand for" | All Remember-level, no depth | Mix in Apply and Analyze questions |
| Regex with `.*` that matches almost anything | Every answer passes, grader learns nothing | Be specific about required tokens |
| YAML in questionText without syntax highlighting | Hard to read | Always use ` ```yaml ` fence |

---

## Full Example Question Set (Services topic)

```json
[
  {
    "id": 1,
    "questionText": "Write the command to list all Services in the `prod` namespace.",
    "image": "",
    "type": "open-cli",
    "tags": ["kubernetes", "service", "kubectl", "command"],
    "gradingCriteria": "kubectl\\s+get\\s+(services|service|svc)(\\s+(-n\\s+|--namespace(=|\\s+))prod|\\s+(--all-namespaces|-A))?",
    "maxPoints": 1
  },
  {
    "id": 2,
    "questionText": "What is the purpose of the `selector` field in a Kubernetes Service?",
    "image": "",
    "type": "open-text",
    "tags": ["kubernetes", "service", "selector", "definition"],
    "gradingCriteria": "The selector is a label-based filter that determines which Pods the Service routes traffic to. Kubernetes uses it to populate the Endpoints object with the IPs of all matching, Ready Pods. If no Pods match the selector, the Endpoints list is empty and traffic is dropped.",
    "maxPoints": 3
  },
  {
    "id": 3,
    "questionText": "You have 4 HTTP microservices and want to expose them all through a single external IP with path-based routing, while minimizing cloud load balancer costs. What is the recommended approach?",
    "image": "",
    "type": "single-choice",
    "tags": ["kubernetes", "service", "ingress", "scenario", "comparison"],
    "options": [
      "Create a LoadBalancer Service for each microservice",
      "Create a NodePort Service for each microservice",
      "Create a ClusterIP Service for each microservice and put an Ingress in front",
      "Create an ExternalName Service that routes to an external load balancer"
    ],
    "correctAnswers": [2],
    "explanation": "Each LoadBalancer Service provisions a separate cloud load balancer, which is expensive. The standard pattern is ClusterIP Services (internal only) exposed through a single Ingress resource that handles path/host routing — one cloud load balancer for all services. NodePort is not suitable for production or cost-effective multi-service setups."
  },
  {
    "id": 4,
    "questionText": "This Service is not routing traffic to any Pod. Identify the bug.\n\n```yaml\napiVersion: v1\nkind: Service\nmetadata:\n  name: api-svc\n  namespace: prod\nspec:\n  selector:\n    app: api-server\n  ports:\n    - port: 80\n      targetPort: 3000\n```\n\nThe running Pods have the label `app: api`.",
    "image": "",
    "type": "single-choice",
    "tags": ["kubernetes", "service", "selector", "debugging", "yaml", "analysis"],
    "options": [
      "The `targetPort` value is incorrect — it should match `port`",
      "The `selector` value `app: api-server` does not match the Pod label `app: api`",
      "A `type` field is required — ClusterIP is not the default",
      "Services cannot be in a named namespace like `prod`"
    ],
    "correctAnswers": [1],
    "explanation": "The selector `app: api-server` does not match any Pod because the Pods have label `app: api`. The Endpoints object will be empty. `ClusterIP` is the default type and does not need to be specified. `targetPort` does not need to match `port`."
  },
  {
    "id": 5,
    "questionText": "Write the YAML for a headless Service named `db-headless` in namespace `data` that targets Pods with label `app: postgres` on port 5432.",
    "image": "",
    "type": "open-code",
    "tags": ["kubernetes", "service", "headless", "statefulset", "yaml", "config-authoring"],
    "gradingCriteria": "yaml: Service manifest with metadata.name=db-headless, metadata.namespace=data, spec.clusterIP=None, spec.selector.app=postgres, spec.ports with port 5432 (targetPort 5432 or same). apiVersion v1 and kind Service required.",
    "maxPoints": 4
  },
  {
    "id": 6,
    "questionText": "Write the command to expose a Deployment named `frontend` as a NodePort Service named `frontend-svc` on port 80, targeting container port 3000, and output the result as YAML without applying it.",
    "image": "",
    "type": "open-cli",
    "tags": ["kubernetes", "service", "nodeport", "kubectl", "dry-run", "command"],
    "gradingCriteria": "kubectl\\s+expose\\s+(deployment|deploy)\\s+frontend\\s+.*--port(=|\\s+)80\\s+.*--target-port(=|\\s+)3000.*--type(=|\\s+)NodePort.*--name(=|\\s+)frontend-svc.*--dry-run(=client)?.*-o(\\s+|=)yaml|kubectl\\s+expose\\s+(deployment|deploy)\\s+frontend\\s+.*--name(=|\\s+)frontend-svc.*--port(=|\\s+)80.*--target-port(=|\\s+)3000.*--type(=|\\s+)NodePort.*--dry-run(=client)?.*-o(\\s+|=)yaml",
    "maxPoints": 1
  },
  {
    "id": 7,
    "questionText": "Which Service types does Kubernetes support? (select all that apply)",
    "image": "",
    "type": "multiple-choice",
    "tags": ["kubernetes", "service", "definition", "remember"],
    "options": [
      "ClusterIP",
      "NodePort",
      "LoadBalancer",
      "ExternalName",
      "InternalName",
      "PublicIP"
    ],
    "correctAnswers": [0, 1, 2, 3],
    "explanation": "Kubernetes has exactly four Service types: ClusterIP (default, internal only), NodePort (exposes on each Node's IP), LoadBalancer (provisions a cloud LB), and ExternalName (DNS CNAME alias). InternalName and PublicIP do not exist."
  },
  {
    "id": 8,
    "questionText": "A Pod in namespace `dev` tries to reach `my-service` but gets a DNS resolution failure. The Service exists in namespace `prod`. What is the correct DNS name to use from the `dev` namespace, and why does the short name fail?",
    "image": "",
    "type": "open-text",
    "tags": ["kubernetes", "dns", "service-discovery", "networking", "debugging", "analysis"],
    "gradingCriteria": "The correct DNS name is 'my-service.prod' or the FQDN 'my-service.prod.svc.cluster.local'. The short name 'my-service' fails because Kubernetes DNS search domains append the Pod's own namespace first — so 'my-service' expands to 'my-service.dev.svc.cluster.local', which does not exist. Cross-namespace resolution requires at least the namespace suffix.",
    "maxPoints": 3
  }
]
```
