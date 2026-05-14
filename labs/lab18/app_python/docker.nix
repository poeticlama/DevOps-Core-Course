{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app pkgs.coreutils ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8080/tcp" = {};
    };
    Env = [
      "PORT=8080"
    ];
  };

  # Reproducible timestamp: Unix epoch start
  # This ensures bit-for-bit identical images on any machine/time
  created = "1970-01-01T00:00:01Z";

  meta = {
    description = "DevOps Info Service Docker image built reproducibly with Nix";
    license = pkgs.lib.licenses.mit;
  };
}

