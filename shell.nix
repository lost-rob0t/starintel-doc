with import <nixpkgs> {};
with pkgs.python310Packages;

stdenv.mkDerivation {
  name = "impurePipenv";
  buildInputs = [
    taglib
    openssl
    git
    libxml2
    libzip
    python310
    pipenv
    stdenv
    libffi
    zlib ];
  src = null;
  shellHook = ''
    pipenv install --dev python-language-server[all] setuptools twine pre-commit
    pipenv install -r requirments.txt
    pipenv shell
  '';
}
