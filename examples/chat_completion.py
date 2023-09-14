import openai

# This is the API base if you are running this locally with a port-forward opened with:
#   kubectl -n logits port-forward svc/logits-ingress-proxy 8080:80
# If you are going to run your app inside the cluster, the API base should instead be:
#   http://logits-api-server.logits.svc.cluster.local:8080/api/v1
# assuming you installed the Helm chart into a namespace called "logits".
openai.api_base = "http://localhost:8080/api/v1"

# We do not currently require API keys on requests to your private API server,
# but the openai client library requires some non-empty value to be set.
openai.api_key = "unused"

completion = openai.ChatCompletion.create(
  model="llama-2-7b-chat",
  messages=[
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello!" }
  ]
)

print(completion.choices[0].message)
