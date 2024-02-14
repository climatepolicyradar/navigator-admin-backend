#!/bin/sh

# Argument is going to be the pull request body.
latest_tag="$1"
echo "Latest tag: ${latest_tag}"

# Extract the version numbers from the tag
version_numbers=${latest_tag#v}       # Remove the leading 'v'
version_numbers=${version_numbers%-*} # Remove the trailing '-beta'

pull_request_body="$2"
echo "${pull_request_body}"

# Check if minor version.
is_minor=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Minor version") -gt 0 ]; then
	is_minor=true
fi

# Check if major version.
is_major=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Major version") -gt 0 ]; then
	is_major=true
fi

# Check if breaking change.
is_breaking_change=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Breaking change") -gt 0 ]; then
	is_breaking_change=true
fi

# If multiple have been checked or none have been checked, don't auto tag.
if { [ "${is_major}" = true ] && [ "${is_minor}" = true ]; } ||
	{ [ "${is_major}" = true ] && [ "${is_breaking_change}" = true ]; } ||
	{ [ "${is_minor}" = true ] && [ "${is_breaking_change}" = true ]; }; then
	echo "Ambiguous tag information. Auto-tagging failed..."
elif { [ "${is_major}" = false ] && [ "${is_minor}" = false ] && [ "${is_breaking_change}" = false ]; }; then
	echo "No tag information found. Auto-tagging failed..."
else
	# Split the version numbers into their respective parts
	breaking_change_version=$(echo "${version_numbers}" | cut -d'.' -f1)
	major_version=$(echo "${version_numbers}" | cut -d'.' -f2)

	# Auto-tag based on selected option.
	if [ "${is_minor}" = true ]; then
		minor_version=$(echo "${version_numbers}" | cut -d'.' -f3)
		new_minor_version=$((minor_version + 1))
		new_tag=v${breaking_change_version}.${major_version}.${new_minor_version}-beta
		echo "Tagging as new minor version ${new_tag}..."
	elif [ "${is_major}" = true ]; then
		new_major_version=$((major_version + 1))
		new_tag="v${breaking_change_version}.${new_major_version}.0-beta"
		echo "Tagging as new major version ${new_tag}..."
	elif [ "${is_breaking_change}" = true ]; then
		new_breaking_version=$((breaking_change_version + 1))
		new_tag=v${new_breaking_version}.0.0-beta
		echo "Tagging as new breaking change ${new_tag}..."
	fi
fi
