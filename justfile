default:
    @just --list

# Sync Plant Safari widget assets from the base iNat-place-safari project
sync-plant-safari *source:
    ./scripts/sync-plant-safari.sh {{source}}

# Build the site directly with a system-installed zola (bypasses the app - useful for quick checks)
build:
    zola build

# Validate content/links directly with a system-installed zola
check:
    zola check
