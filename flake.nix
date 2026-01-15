{
  description = "Document Spec for Star intel";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      # Custom ulid-py dependency
      ulid-py = pkgs.python312Packages.buildPythonPackage rec {
        pname = "ulid-py";
        version = "1.1.0";
        format = "setuptools";

        src = pkgs.fetchPypi {
          inherit pname version;
          hash = "sha256-3GiEvpFVjfB3wwEbn7DIfRCXy4/GU0sR8xAWGv1XOPA=";
        };

        doCheck = false;

        meta = with pkgs.lib; {
          description = "Universally Unique Lexicographically Sortable Identifier (ULID) in Python";
          homepage = "https://github.com/mdomke/python-ulid";
          license = licenses.mit;
        };
      };

      # Main starintel_doc package
      starintel-doc = pkgs.python312Packages.buildPythonPackage rec {
        pname = "starintel_doc";
        version = "0.8.2";
        format = "setuptools";

        src = ./.;

        propagatedBuildInputs = with pkgs.python312Packages; [
          ulid-py
          dataclasses-json
        ];

        doCheck = false;

        meta = with pkgs.lib; {
          description = "Document Spec for Star intel";
          homepage = "https://github.com/lost-rob0t/starintel_doc";
          license = licenses.mit;
        };
      };

    in {
      packages.${system} = {
        default = starintel-doc;
        starintel-doc = starintel-doc;
        ulid-py = ulid-py;
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          python312Packages.pip
          python312Packages.setuptools
          python312Packages.wheel
        ] ++ [
          ulid-py
        ];

        shellHook = ''
          export PYTHONPATH="${starintel-doc}/${pkgs.python312.sitePackages}:$PYTHONPATH"
          echo "StarIntel Doc dev environment ready"
          echo "Python: $(python --version)"
          echo "Package version: ${starintel-doc.version}"
        '';
      };

      # Apps for easy running
      apps.${system} = {
        default = {
          type = "app";
          program = "${pkgs.python312.withPackages (ps: [ starintel-doc ])}/bin/python";
        };
      };
    };
}
