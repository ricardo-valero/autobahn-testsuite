{
  description = "Autobahn|Testsuite dev environment: host tooling (just, uv) plus CPython 2.7.18 for native wstest runs";

  nixConfig = {
    # Binary cache for nixpkgs-python's CPython builds (avoids compiling 2.7.18 locally)
    extra-substituters = "https://nixpkgs-python.cachix.org";
    extra-trusted-public-keys = "nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuu4mEXs=";
  };

  inputs = {
    # Pinned to 26.05: the last nixpkgs release supporting x86_64-darwin
    # (unstable/26.11 dropped it; 26.05 receives security fixes until end of 2026).
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-26.05-darwin";
    nixpkgs-python = {
      url = "github:cachix/nixpkgs-python";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixpkgs-python }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems f;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.permittedInsecurePackages = [
              # The pinned py2 stack (cryptography 3.3.2) only builds against OpenSSL 1.1,
              # the same 1.1.1w the frozen Docker reference image uses.
              "openssl-1.1.1w"
            ];
          };
          python2 = nixpkgs-python.packages.${system}."2.7.18";
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.just
              pkgs.uv
              pkgs.python312   # Python 3 runtime for the migrate-python3 port
              python2          # frozen py2 toolchain (retired in a follow-up change)
              pkgs.pkg-config
              pkgs.libffi
              pkgs.openssl_1_1
            ];

            shellHook = ''
              # The nixpkgs-python CPython is UCS-4 (cp27mu), so PyPI's cp27m macOS wheels
              # don't apply: cffi/cryptography build from source and need these headers.
              # -Wno-error=...: the pinned C extensions predate modern clang, which promotes
              # implicit function declarations to errors.
              export PKG_CONFIG_PATH="${pkgs.libffi.dev}/lib/pkgconfig:${pkgs.openssl_1_1.dev}/lib/pkgconfig''${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
              export CFLAGS="-Wno-error=implicit-function-declaration -I${pkgs.libffi.dev}/include -I${pkgs.openssl_1_1.dev}/include"
              export LDFLAGS="-L${pkgs.libffi}/lib -L${pkgs.openssl_1_1.out}/lib"

              echo "autobahn-testsuite dev shell (just, uv, python2 $(python2 --version 2>&1 | awk '{print $2}'))"
              echo "  native py2 venv (dev iteration):  uvx 'virtualenv<20.22' -p python2 .venvs/cpy27"
              echo "  conformance reference (reports):  just docker-test  (frozen pypy:2-7 Docker image)"
            '';
          };
        });
    };
}
