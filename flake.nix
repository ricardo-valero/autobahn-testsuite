{
  description = "Autobahn|Testsuite — Python 3 dev environment (uv + nix)";

  inputs = {
    # Pinned to 26.05: the last nixpkgs release supporting x86_64-darwin.
    # Follow-up: switch back to nixpkgs-unstable once the dev machine is Apple Silicon.
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-26.05-darwin";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    systems = nixpkgs.lib.systems.flakeExposed;
    forAllSystems = nixpkgs.lib.genAttrs systems;
  in {
    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.alejandra);

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      default = pkgs.mkShell {
        packages = builtins.attrValues {
          inherit (pkgs) just uv nixd alejandra;
          python = pkgs.python3.withPackages (p: builtins.attrValues {inherit (p) uv;});
        };

        shellHook = ''
          echo "autobahn-testsuite dev shell — python3 $(python3 --version 2>&1 | awk '{print $2}'), uv $(uv --version 2>&1 | awk '{print $2}')"
          echo "  contributor:  uv sync  →  uv run wstest -m fuzzingserver   (or: just run)"
          echo "  end users:    uvx autobahntestsuite   |   pip install autobahntestsuite"
        '';
      };
    });
  };
}
