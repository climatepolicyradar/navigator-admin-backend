#!/bin/sh

pull_request_body="$1"

# Get the latest Git tag.
git fetch --prune --unshallow --tags
latest_tag=$(git tag --list 'v*' --sort=-authordate --merged | head -n1)
echo "Latest tag: ${latest_tag}"

# Extract the version numbers from the tag
version_numbers=${latest_tag#v}       # Remove the leading 'v'
version_numbers=${version_numbers%-*} # Remove the trailing '-beta'

# Check if patch version.
is_patch=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Patch") -gt 0 ]; then
	is_patch=true
fi

# Check if minor version.
is_minor=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Minor version") -gt 0 ]; then
	is_minor=true
fi

# Check if major change.
is_major=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Major version") -gt 0 ]; then
	is_major=true
fi

# If multiple have been checked or none have been checked, don't auto tag.
if { [ "${is_minor}" = true ] && [ "${is_patch}" = true ]; } ||
	{ [ "${is_minor}" = true ] && [ "${is_major}" = true ]; } ||
	{ [ "${is_patch}" = true ] && [ "${is_major}" = true ]; }; then
	echo "Ambiguous tag information. Auto-tagging failed..."
elif { [ "${is_minor}" = false ] && [ "${is_patch}" = false ] && [ "${is_major}" = false ]; }; then
	echo "No tag information found. Auto-tagging failed..."
else
	# Split the version numbers into their respective parts
	major_change_version=$(echo "${version_numbers}" | cut -d'.' -f1)
	minor_version=$(echo "${version_numbers}" | cut -d'.' -f2)

	# Auto-tag based on selected option.
	if [ "${is_patch}" = true ]; then
		patch_version=$(echo "${version_numbers}" | cut -d'.' -f3)
		new_patch_version=$((patch_version + 1))
		new_tag=v${major_change_version}.${minor_version}.${new_patch_version}-beta
		echo "Tagging as new patch ${new_tag}..."
	elif [ "${is_minor}" = true ]; then
		new_minor_version=$((minor_version + 1))
		new_tag="v${major_change_version}.${new_minor_version}.0-beta"
		echo "Tagging as new minor version ${new_tag}..."
	elif [ "${is_major}" = true ]; then
		new_major_version=$((major_change_version + 1))
		new_tag=v${new_major_version}.0.0-beta
		echo "Tagging as new major version ${new_tag}..."
	fi
fi
