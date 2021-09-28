# jsonmerge git merge driver

### Purpose

Simple demo of configuring a custom Git merge driver to merge JSON files stored in a Git repository.

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

### Potential Extension: using additional files in the repo to assist resolving merges




### References

1.	[How to wire a custom merge driver in to git (git-scm.com)](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver)
2.	[What values you can pass in to the merge driver on the command line (github.com/git/git)](# https://github.com/git/git/blob/f1d4a28250629ae469fc5dd59ab843cb2fd68e12/ll-merge.c)
3.	[Simple example of the plumbing to wire in a merge driver, with a trivial dumb driver script (github.com/Praqma/git-merge-driver)](https://github.com/Praqma/git-merge-driver)
4.	[Undocumented ways to discover what branches are involved during a merge driver conflict. Does not work reliably in all situations -- e.g. stashing, rebase. (stackoverflow.com)](Ref: https://stackoverflow.com/questions/24302644/how-to-retrieve-branch-names-in-a-custom-git-merge-driver)
5.	[Workflow for auto-merging conflicts in structured game content (bitsquid.blogspot.com)](http://bitsquid.blogspot.com/2010/06/avoiding-content-locks-and-conflicts-3.html)

