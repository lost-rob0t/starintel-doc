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

      mkPackageSet = pkgs:
        let
          ulidPy = pkgs.python3Packages.buildPythonPackage {
            pname = "ulid-py";
            version = "1.1.0";
            pyproject = true;

            src = pkgs.fetchPypi {
              pname = "ulid-py";
              version = "1.1.0";
              hash = "sha256-3GiEvpFVjfB3wwEbn7DIfRCXy4/GU0sR8xAWGv1XOPA=";
            };

            build-system = with pkgs.python3Packages; [
              setuptools
            ];

            pythonImportsCheck = [ "ulid" ];
            doCheck = false;
          };

          starintelDoc = pkgs.python3Packages.buildPythonPackage {
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
            ] ++ [
              ulidPy
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
          inherit ulidPy starintelDoc;
        };
    in
    {
      packages = forAllSystems (system:
        let
          packageSet = mkPackageSet nixpkgs.legacyPackages.${system};
        in
        {
          default = packageSet.starintelDoc;
          starintel-doc = packageSet.starintelDoc;
          ulid-py = packageSet.ulidPy;
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

      overlays.default = final: _prev:
        let
          packageSet = mkPackageSet final;
        in
        {
          starintel-doc = packageSet.starintelDoc;
          ulid-py = packageSet.ulidPy;
        };
    };
}
