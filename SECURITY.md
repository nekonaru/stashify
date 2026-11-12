# Security Policy

## Reporting a vulnerability

Please report security issues privately by opening a security advisory:

https://github.com/nekonaru/stashify/security/advisories/new

Do not open a public issue for a suspected vulnerability. We aim to
acknowledge reports within 7 days.

## Scope

Stashify is a command line tool. It runs on your machine, reads files you
choose and reaches out to the Spotify Web API, the YouTube service (through
yt-dlp) and a community lyrics endpoint. It does not listen on any network
port and it does not store credentials on disk.

## What you should know

- Your Spotify client id and secret are read from the environment, or from
  command line flags. They are never written to disk by Stashify.
- Stashify does not verify or claim ownership of the music it downloads.
  You are responsible for how you use it.
