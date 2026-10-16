cask "pi" do
  arch arm: "arm64", intel: "x64"

  version :latest
  sha256 :no_check

  url "https://github.com/earendil-works/pi/releases/latest/download/pi-darwin-#{arch}.tar.gz"
  name "Pi"
  desc "Extensible terminal coding agent"
  homepage "https://pi.dev/"

  depends_on :macos

  binary "pi/pi"

  caveats <<~EOS
    Update the Pi executable with `brew upgrade pi`, not Pi's self-updater.
    To include Pi in a general `brew upgrade`, add
    HOMEBREW_UPGRADE_GREEDY_CASKS=pi to your Homebrew environment file.
  EOS
end
