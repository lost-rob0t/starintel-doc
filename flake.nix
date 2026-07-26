{
  description = "StarIntel v0.9.0 document specification for Python";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs systems;

      mkPackage = pkgs:
        pkgs.python3Packages.buildPythonPackage {
          pname = "starintel-doc";
          version = "0.9.0";
          pyproject = true;
          src = self;

          build-system = with pkgs.python3Packages; [
            setuptools
          ];

          dependencies = with pkgs.python3Packages; [
            dataclasses-json
            jsonschema
            ulid-py
          ];

          pythonImportsCheck = [ "starintel_doc" ];
          doCheck = false;

          meta = {
            description = "StarIntel v0.9.0 document parser, validator, and serializer";
            homepage = "https://github.com/lost-rob0t/starintel-doc";
            mainProgram = "starintel-conformance";
          };
        };
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          package = mkPackage pkgs;
        in
        {
          default = package;
          starintel-doc = package;
        });

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.starintel-doc}/bin/starintel-conformance";
        };

        starintel-conformance = {
          type = "app";
          program = "${self.packages.${system}.starintel-doc}/bin/starintel-conformance";
        };
      });

      checks = forAllSystems (system: {
        default = self.packages.${system}.starintel-doc;
      });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          package = self.packages.${system}.starintel-doc;
          python = pkgs.python3.withPackages (_: [ package ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.python3Packages.build
              pkgs.python3Packages.setuptools
            ];
          };
        });

      overlays.default = final: _prev: {
        starintel-doc = mkPackage final;
      };
    };
}
