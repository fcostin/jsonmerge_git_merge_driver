# jsonmerge git merge driver

### Purpose

Simple demo custom Git merge driver to merge JSON objects stored in `*.json` files in a Git repository.

The script is not production quality but provides an example of the

### Demo JSON object custom merge strategy

Two limited merge strategies are supported:

1.  if the source and destination files are equal when interpreted as JSON objects,
    merge them as that JSON value, written to file in a normalised format.

2.  if the source and destimation files are not equal when interpreted as JSON objects,
    check that the source, destination and base JSON values are all JSON objects
    with the same top-level keys. If they are, compute a shallow merge using top-level
    key value pairs:
    *   compute a top-level attribute patch between the base JSON value and the source JSON value
    *   apply the top-level attribute patch to the destination JSON value
    The result is deemed the merged JSON value.
    Write the merged JSON value to file in a normalised format.

Not-supported

*   merging inside git stash
*   merging inside git rebase
*   merging files that are not JSON files
*   octopus merges


Note that there are many scenarios not covered by strategy 1 or 2. In this case this
merge tool gives up and returns nonzero, which puts git into the merge conflict state.

Note that the automatic merge strategies may not do what you want.

It is plausible that strategy 2 may not do what you want in some cases: the
strategy regards the patch from base to source as having higher priority
than the patch from base to destination, and resolves conflicts according to
priority. This precedence might not make sense for your workflow.


### Repository configuration

#### `.git/config` file

Add the following section to the repository `.git/config` file:

```
[merge "jsonmerge-driver"]
        driver = python3 jsonmerge.py %P %O %A %B
```

The protocol that our custom merge driver script is expected to follow is
documented in `ll-merge.c` in the git source code:

```
/*
 * merge.<name>.driver specifies the command line:
 *
 *	command-line
 *
 * The command-line will be interpolated with the following
 * tokens and is given to the shell:
 *
 *    %O - temporary file name for the merge base.
 *    %A - temporary file name for our version.
 *    %B - temporary file name for the other branches' version.
 *    %L - conflict marker length
 *    %P - the original path (safely quoted for the shell)
 *
 * The external merge driver should write the results in the
 * file named by %A, and signal that it has done with zero exit
 * status.
 */
```

### `.gitattributes` file

Ensure a `.gitattributes` file exists within the root of the
repository, containing the following:

```
*.json merge=jsonmerge-driver
```

This line instructs git to invoke the `jsonmerge-driver` when
merging files that match the pattern `*.json`.

### Possible extension: schema-aware JSON merge strategy

When version controlling JSON values containing structured data,
a natural thing to do might be to define a schema for the JSON
values, using [JSON Schema](https://json-schema.org/). If we know
that a particular JSON value stored as a file in the git repo
should satisfy some particular JSON Schema, we might want the JSON
merge driver to be aware of that Schema and, where the result of
a merge is ambiguous, prefer a merge result that satisifes the
schema.  In order to implement something like this, the merge
driver would need a way to figure out the schema associated with
a JSON file when merging that file. One way to do this could be
to version control the JSON Schemas as files stored in the same
git repo, and extend the JSON merge driver script with the
capability to discover and load those schemas. Some details
would need to be pinned down, such as which branch or version of
the schema should be loaded?

### References

1.	[How to wire a custom merge driver in to git (git-scm.com)](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver)
2.	[What values you can pass in to the merge driver on the command line (github.com/git/git)](# https://github.com/git/git/blob/f1d4a28250629ae469fc5dd59ab843cb2fd68e12/ll-merge.c)
3.	[Simple example of the plumbing to wire in a merge driver, with a trivial dumb driver script (github.com/Praqma/git-merge-driver)](https://github.com/Praqma/git-merge-driver)
4.	[Undocumented ways to discover what branches are involved during a merge driver conflict. Does not work reliably in all situations -- e.g. stashing, rebase. (stackoverflow.com)](Ref: https://stackoverflow.com/questions/24302644/how-to-retrieve-branch-names-in-a-custom-git-merge-driver)
5.	[Workflow for auto-merging conflicts in structured game content (bitsquid.blogspot.com)](http://bitsquid.blogspot.com/2010/06/avoiding-content-locks-and-conflicts-3.html)

