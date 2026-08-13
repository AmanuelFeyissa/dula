{{/* Common naming + label helpers. Per-component resource names are `<release>-<component>`. */}}

{{- define "dula.labels" -}}
app.kubernetes.io/name: dula
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: dula
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/* Per-component selector labels. Call with a dict {root, name}. */}}
{{- define "dula.selectorLabels" -}}
app.kubernetes.io/name: dula
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .name }}
{{- end -}}

{{/* Fully-qualified image reference for a component (digest-pinned in prod overlays). */}}
{{- define "dula.image" -}}
{{- $root := .root -}}{{- $c := .c -}}
{{- $registry := $root.Values.global.imageRegistry | trimSuffix "/" -}}
{{- if hasPrefix "sha256:" (toString $root.Values.global.imageTag) -}}
{{- printf "%s/%s@%s" $registry $c.image $root.Values.global.imageTag -}}
{{- else -}}
{{- printf "%s/%s:%s" $registry $c.image (toString $root.Values.global.imageTag) -}}
{{- end -}}
{{- end -}}

{{- define "dula.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default "dula" .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
