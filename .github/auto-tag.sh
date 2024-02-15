#!/bin/bash
# set -e

script_folder=$(dirname "${BASH_SOURCE[0]}")
source $script_folder/funcs.sh

# Get the latest Git tag.
git fetch --prune --unshallow --tags # This is needed - without it no tags are found.
latest_tag=$(git tag --list 'v*' --sort=-authordate --merged | head -n1)
if [ -z "${latest_tag}" ]; then
	echo "No tags found. Please create first tag manually to enable auto-tagging."
	exit 1
fi
echo "Latest tag: ${latest_tag}"

# Extract the version numbers from the tag
version_numbers=${latest_tag#v}       # Remove the leading 'v'
version_numbers=${version_numbers%-*} # Remove the trailing '-beta'

pr_body="$1"

# Check if patch version.
is_patch=false
if [ $(echo "${pr_body}" | grep -c "\[x\] Patch") -gt 0 ]; then
	is_patch=true
fi

# Check if minor version.
is_minor=false
if [ $(echo "${pr_body}" | grep -c "\[x\] Minor version") -gt 0 ]; then
	is_minor=true
fi

# Check if major change.
is_major=false
if [ $(echo "${pr_body}" | grep -c "\[x\] Major version") -gt 0 ]; then
	is_major=true
fi

# If multiple have been checked or none have been checked, don't auto tag.
pr_number="$2"
if { [ "${is_minor}" = true ] && [ "${is_patch}" = true ]; } ||
	{ [ "${is_minor}" = true ] && [ "${is_major}" = true ]; } ||
	{ [ "${is_patch}" = true ] && [ "${is_major}" = true ]; }; then
	echo "Ambiguous tag information in body of pull request #${pr_number}. Auto-tagging failed..."
	exit 1
elif { [ "${is_minor}" = false ] && [ "${is_patch}" = false ] && [ "${is_major}" = false ]; }; then
	echo "No tag information found in body of pull request #${pr_number}. Auto-tagging failed..."
	exit 1
else
	# Split the version numbers into their respective parts
	major_version=$(get_major "${version_numbers}")
	minor_version=$(get_minor "${version_numbers}")

	maturity=$(get_maturity "${version_numbers}")
	echo "Maturity: ${maturity}"

	# Auto-tag based on selected option.
	if [ "${is_patch}" = true ]; then
		patch_version=$(get_patch "${version_numbers}")
		new_patch_version=$(increment "${patch_version}")
		new_tag=v${major_version}.${minor_version}.${new_patch_version}-beta
		echo "Tagging as new patch ${new_tag}..."
	elif [ "${is_minor}" = true ]; then
		new_minor_version=$(increment "${minor_version}")
		new_tag="v${major_version}.${new_minor_version}.0-beta"
		echo "Tagging as new minor version ${new_tag}..."
	elif [ "${is_major}" = true ]; then
		new_major_version=$(increment "${major_version}")
		new_tag=v${new_major_version}.0.0-beta
		echo "Tagging as new major version ${new_tag}..."
	fi
fi
