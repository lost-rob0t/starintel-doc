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
    curl
    ispell
    zlib ];
  src = null;
  shellHook = ''
    pipenv shell
  '';
}
