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
maturity=$(get_maturity "${latest_tag}")
echo "Maturity: ${latest_tag}"
version_numbers=${latest_tag#v}       # Remove the leading 'v'
version_numbers=${version_numbers%-*} # Remove the trailing '-beta'

pr_body="$1"

# Get selected versioning checkboxes.
is_patch=$(is_patch_selected "${pr_body}")
is_minor=$(is_minor_selected "${pr_body}")
is_major=$(is_major_selected "${pr_body}")

# If multiple have been checked or none have been checked, don't auto tag.
pr_number="$2"
if { [[ "${is_minor}" ]] && [[ "${is_patch}" ]]; } ||
	{ [[ "${is_minor}" ]] && [[ "${is_major}" ]]; } ||
	{ [[ "${is_patch}" ]] && [[ "${is_major}" ]]; }; then
	echo "Ambiguous tag information in body of pull request #${pr_number}. Auto-tagging failed..."
	exit 1
elif { [[ ! ${is_minor} == 0 ]] && [[ ! ${is_patch} == 0 ]] && [[ ! ${is_major} == 0 ]]; }; then
	echo "No tag information found in body of pull request #${pr_number}. Auto-tagging failed..."
	exit 1
else
	# Split the version numbers into their respective parts
	major_version=$(get_major "${version_numbers}")
	minor_version=$(get_minor "${version_numbers}")

	# Auto-tag based on selected option.
	if [[ "${is_patch}" ]]; then
		patch_version=$(get_patch "${version_numbers}")
		new_patch_version=$(increment "${patch_version}")
		new_tag=v${major_version}.${minor_version}.${new_patch_version}-beta
		echo "Tagging as new patch ${new_tag}..."
	elif [[ "${is_minor}" ]]; then
		new_minor_version=$(increment "${minor_version}")
		new_tag="v${major_version}.${new_minor_version}.0-beta"
		echo "Tagging as new minor version ${new_tag}..."
	elif [[ "${is_major}" ]]; then
		new_major_version=$(increment "${major_version}")
		new_tag=v${new_major_version}.0.0-beta
		echo "Tagging as new major version ${new_tag}..."
	fi
fi
