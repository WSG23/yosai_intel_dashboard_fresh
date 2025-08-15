path "transit/keys/*" {
  capabilities = ["read"]
}

path "transit/encrypt/*" {
  capabilities = ["update"]
}

path "transit/decrypt/*" {
  capabilities = ["update"]
}
