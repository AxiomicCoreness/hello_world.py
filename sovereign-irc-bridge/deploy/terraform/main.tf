# Stub: provisions cluster / secrets manager out of band.
# No live credentials in-repo. Wire remote state + secret manager in a follow-up.
terraform {
  required_version = ">= 1.5"
}

variable "irc_host" {
  type    = string
  default = "irc.abjects.net"
}

output "irc_host" {
  value = var.irc_host
}

# Intentionally empty resource block — apply is gated by deploy workflow KUBECONFIG.
