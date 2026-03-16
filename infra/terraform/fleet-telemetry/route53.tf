# DNS record for Fleet Telemetry server

resource "aws_route53_record" "fleet_telemetry" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.fqdn
  type    = "A"

  alias {
    name                   = aws_lb.fleet_telemetry.dns_name
    zone_id                = aws_lb.fleet_telemetry.zone_id
    evaluate_target_health = true
  }
}
