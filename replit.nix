{pkgs}: {
  deps = [
    pkgs.sqlite-interactive
    pkgs.postgresql
    pkgs.openssl
    pkgs.sqlite
  ];
}
