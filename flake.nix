{
  description = "intake feed sources";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/22.11";

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    devShells.${system} = {
      intake-rss = let
        pythonEnv = pkgs.python38.withPackages (pypkgs: with pypkgs; [ black feedparser ]);
      in pkgs.mkShell {
        packages = [ pythonEnv ];
        shellHook = ''
          PS1="(intake-rss) $PS1"
        '';
      };
    };
  };
}

