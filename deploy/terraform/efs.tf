resource "aws_efs_file_system" "qdrant" {
  creation_token   = "${local.name_prefix}-qdrant"
  performance_mode = "generalPurpose"
  encrypted        = true
  tags             = merge(local.common_tags, { Name = "${local.name_prefix}-qdrant" })
}

resource "aws_efs_mount_target" "qdrant" {
  for_each        = data.aws_subnet.selected
  file_system_id  = aws_efs_file_system.qdrant.id
  subnet_id       = each.value.id
  security_groups = [aws_security_group.efs.id]
}
