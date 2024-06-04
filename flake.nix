{
  description = "Save your repl session, ignoring errors";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=23.05";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
      in {
        packages = {
            default = pkgs.stdenv.mkDerivation {
                name = "morji";
                src = ./.;
                buildInputs = with pkgs; [
                    gcc
                    gnumake
                ];
                propagatedBuildInputs = [
                    python
                ];
                buildPhase = ''
                    echo 'helllooooo'
                    make PYTHON_INCLUDE=${python}/include/$(ls ${python}/include)
                '';
                installPhase = ''
                    mkdir -p $out/bin
                    cp -r morji $out/
                    echo '#!/bin/sh' > $out/bin/morji
                    echo 'python3 '$out'/morji $@' >> $out/bin/morji
                    chmod +x $out/bin/morji
                '';
            };
        };
      });
}
