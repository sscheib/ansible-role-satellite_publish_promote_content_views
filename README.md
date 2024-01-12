[![ansible-lint](https://github.com/sscheib/ansible-role-satellite_publish_promote_content_views/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/sscheib/ansible-role-satellite_publish_promote_content_views/actions/workflows/ansible-lint.yml) [![Publish latest release to Ansible Galaxy](https://github.com/sscheib/ansible-role-satellite_publish_promote_content_views/actions/workflows/ansible-galaxy.yml/badge.svg)](https://github.com/sscheib/ansible-role-satellite_publish_promote_content_views/actions/workflows/ansible-galaxy.yml)

satellite_content_view_version_publish_promote
=========

**A word of caution upfront:**

This role is absurdly complex. I tested as best as I could, but I certainly cannot guarantee that there are no bugs left. Since Repository synchronization, Content View publish and/or promote
actions *will* change these objects in your Satellite, I'd urge you to test prior to using this in production right away. This role is provided "as is" and I do not take responsibility for any potential
devastating consequences it might have. Please keep that in mind and test with a snapshot in place for your Satellite or on a lab system. Thanks a lot :slightly_smiling_face:



This role publishes and optionally promotes both Content View and Composite Content view versions. It makes use of the Red Hat certified
collection [`redhat.satellite`](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/docs/).

To use the certified collection `redhat.satellite` you need to be a Red Hat subscriber. If you don't own any subscriptions, you can make use of
[Red Hat's Developer Subscription](https://developers.redhat.com/articles/faqs-no-cost-red-hat-enterprise-linux) which is provided at no cost by Red Hat.

You can also make use of the upstream collection [`theforeman.foreman`](https://docs.ansible.com/ansible/latest/collections/theforeman/foreman/index.html), but you'd need to
change the module names from `redhat.satellite` to `theforeman.foreman` - but I have *not* tested this.

The role was written in such a way that it accepts the variable definition of Content Views the same way the role 
[`redhat.satellite.content_view_publish`](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/content/role/content_view_publish/) does.

It also supports the [Common Role Variables](https://github.com/theforeman/foreman-ansible-modules/blob/develop/README.md#common-role-variables) for the `redhat.satellite` collection.
The `redhat.satellite` GitHub Repository does not contain a section about which common role variables can be used, but these can be checked in the
[code](https://github.com/RedHatSatellite/satellite-ansible-collection/blob/develop/plugins/module_utils/foreman_helper.py#L368-L371) directly.

The common role variables are:
- `SATELLITE_SERVER_URL`, `SATELLITE_SERVER`, `SATELLITE_URL`
- `SATELLITE_USERNAME`, `SATELLITE_USER`
- `SATELLITE_PASSWORD`
- `SATELLITE_VALIDATE_CERTS`

Reusing the same Content View definition as the `redhat.satellite` collection, enables you to keep the same YAML definition for your Content Views/Composite Content Views,
although I strongly recommend migrating your YAML definition to a more 'modern' definition, which both Foreman and the Satellite roles and this one accept.

To ease this process, you can run this role with the tag `convert` (`--tags convert`) which will store the converted YAML into a file of your choice, which you'd also need to specify with
the variable `sat_convert_yaml_file`.

The conversion is done by default with a custom filter shipped with this role (`list_of_dicts_to_indented_yaml`). This filter essentially indents the lists 'correctly' by two spaces, which
`ansible.builtin.to_nice_yaml` does not (which is a [Limitation](https://github.com/ansible/ansible/issues/66932) that is known about and which likely is not easy to resolve,
in case you wondered). The filter `list_of_dicts_to_indented_yaml` also adds the possibility to put a specific key and value to the top of a list of dictionaries (by default `name`).

Please note that this filter is **not** meant for using it outside this role (that's why I also went for the worst name I could :slightly_smiling_face:). It will only accept a list of 
dictionaries (as that's what the conversion will generate) and error out on any other data type. Implementing YAML parsing for a variety of data types is a beast on its on own.
For this particular use-case the role has, the shipped filter does the job well.

The reason I strongly recommend migrating off the 'legacy'[^legacy] YAML definitions is, that this role needs the definition to be in a specific way for it to work. Don't worry, it converts
it on-the-fly, but this is at the cost of a performance hit as it needs to iterate through all Content View/Composite Content View definitions and convert each of them. The bigger your Content
View/Composite Content View definition is the bigger the performance impact.

The only thing that this role does not accept as argument but the others did: `current_lifecycle_environment`. The role has a different approach, as it figures out the current Lifecycle
Environment/s for every Content View version/Composite Content View version dynamically and therefore does not require this argument.

Leaving `current_lifecycle_environment` defined in your Content View/Composite Content View definition won't bother this role, as this attribute is never retrieved.

The role adds some attributes to the definition of `satellite_content_views` (which the other roles will not care about):
- `patch_day_exclude`: With this you can permanently exclude a Content View/Composite Content View from being processed. These would be Content Views/Composite Content Views you only ever touch on
   "special occasions". For instance, when you perform a Satellite update :slightly_smiling_face:. This attribute is *optional*.
- `lifecycle_environments`: A list of Lifecycle Environments (also per Content View/Composite Content View) to promote the Content View/Composite Content View to. This list can be cut down (see
   the variables section below) on demand. This attribute is *optional* for publishing, but *mandatory* for promoting.

## Differences to `redhat.satellite.content_view_publish` 

The way this role works, is completely different compared to the way the role `redhat.satellite.content_view_publish` works.

The role `redhat.satellite.content_view_publish` is as straight forward as it can get: Publish all Content Views defined in `satellite_content_views` by iterating over that list and publish them.
Either asynchronously (`async`) or one after another. No bells and whistles. Don't get me wrong, it is absolutely nothing wrong with this role. The way it works is probably exactly what 98% of the
users of the role appreciate.

I am one of the 2% that need more than that. I want to the role to dynamically decide what Content Views/Composite Content Views to publish, where to promote them to and even
exclude Content Views/Composite Content Views without redefining `satellite_content_views`.
Moreover, I do not want the role to publish a new Content View/Composite Content View version if it is not required, because nothing has changed. The same for promotion. It should only promote if it
is necessary and therefore only report a `changed` status *if* something really has changed. Of course, I also want to limit the Lifecycle Environments it promotes to - and not by redefining the
definition in `satellite_content_views`.

Sounds too good to be true? Well, kind of. I have implemented all of the above (and more) in this role, but that has its downsides: Complexity and execution speed.

I did my best to cut the execution speed as low as possible, but it is significantly slower than `redhat.satellite.content_view_publish` - but also more versatile.

To implement the above outlined requirements, I'd technically need to retrieve each Content View/Composite Content View one by one from the Satellite API and extract the data required. This can
surely be done while iterating over all Content Views/Composite Content Views and executing `redhat.satellite.resource_info` for the currently being iterated Content View/Composite Content View.

Or, we just retrieve *all* Content Views/Composite Content Views at once and filter out those which are not defined in `satellite_content_views`. Retrieving a "big blob" of data from the Satellite
API is *usually* quicker in my experience than retrieving little chunks one by one. After all, you'd most likely publish and/or promote all Content Views/Composite Content Views which are 
present in the Satellite and might exclude only a handful. So ultimately, we'd need to retrieve the majority of the Content Views/Composite Content Views anyway, so why not
retrieve them all at once :slightly_smiling_face:.

I also have **a ton** of checks in place to ensure that both data fed into the role and data retrieved from the Satellite API are as *expected*. I know, this is not very Ansible'ish, but I want to make
absolutely sure *everything* is as expected as it can get, which will prevent unexpected outcomes.

All of the above make the role very versatile, but very complex at the same time. I commented complex sections in the code the best I could to ensure users of this role understand what's happening.

But let's be honest. This role is nothing for Ansible beginners. You could even argue, that most of the code in this role should be handled by a dedicated Ansible module and what I am doing with 
this role is just pure insanity. You might be right. But I also think that this kind of code is not as uncommon as one might assume. After all, Ansible is great in connecting different systems and for
that you sometimes need complexity. Unfortunately.

## When to consider using this role

You can consider using this role over the official `redhat.satellite.content_view_publish` when:
1. You want to promote Content View versions or Composite Content View versions while publishing a new Content View version/Composite Content View version
2. You want to promote *only*, without publishing a new Content View version or Composite Content View version, which is idempotent.
3. You want to promote, but only to defined Lifecycle Environments in an idempotent way
4. You have the need to exclude certain Content Views or certain Composite Content views from publishing or promoting during regular patch days
5. You don't want to worry about the order you define the Content Views or Composite Content Views in
6. You want to 'dynamically' limit the Lifecycle Environments Content View versions are promoted to, without redefining the YAML for the Content View versions or Composite
   Content view versions. This is useful if you patch, say, every week. But on Monday's you'd only like to promote to `dev`, on Tuesday to `qa` and on
   Thursday to `prod`.
7. You want to publish and optionally promote a Content View based on the whether the latest Content View version is older than the
   last synchronization date of the included repositories
8. You want to publish and optionally promote Composite Content Views only then, if the included Components (Content View version) have been updated since the last publish
   of the Composite Content View
9. You want to ensure that prior to publishing all Repositories are:
   - Synchronized
   - Finished their last synchronization successfully
   - Are not currently synchronizing
10. You want to synchronize Repositories prior to publishing and optionally promoting Content Views/Composite Content Views
11. You want to exclude certain Repositories from checking and/or synchronizing
12. You want to wait for currently synchronizing Repositories (when *not* triggered via this role) to finish prior publishing and optionally promoting Content Views/Composite Content Views

## Why didn't you contribute to the Red Hat certified collection/the upstream Foreman Ansible collection?

I might ask if such a role is something that is worth contributing. It could theoretically be a drop-in replacement for the existing role `content_view_publish`, but it is 
significantly more complex and has a different approach when it comes to validating data (user provided or API). This role validates *everything* to ensure nothing
breaks during patch days, which is something I worry more about than the execution speed of the role itself.
It also contains quite a bit of rather complex YAML-multiline-filter 'madness' (although in my opinion very well commented), which *might* be something others won't like.

I wrote this role primarily for myself, as I need it exactly the way it is. It *might* be something for the broader audience, but whether that's something Red Hat or the Foreman community
wants to entertain in the long run (even if I sign up as maintainer for this particular role), is a different story.

As always with Open Source, I cannot guarantee that I will maintain this role for the next three, five, ten or more years, so a new maintainer needs to be found when it is part of the
`redhat.satellite` and/or `theforeman.foreman` collection should I vanish for whatever reason. Although I absolutely plan maintaining this role for quite some time, I can certainly not
guarantee it. If it is deemed too complex to maintain for others, it is probably not going to make it into either of the collections.

Honestly: Don't hold your breath for it, as it is most definitively too complex, unfortunately :pensive:.

## What this role considers as 'legacy' definition

[^legacy]: The roles [`redhat.satellite.content_view_publish`](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/content/role/content_view_publish/) and
also the role [`theforeman.foreman.content_view_publish`](https://github.com/theforeman/foreman-ansible-modules/tree/develop/roles/content_view_publish/tasks) accept Content View/Composite
Content View definitions in the following formats:

### Format one, which I call `legacy_a`

```
satellite_content_views:
- 'content_view_name1'
- 'content_view_name2'
- 'content_view_name3'
- etc.
```

### Format two, which I call `legacy_b`

```
satellite_content_views:
- content_view: 'content_view_name1'
- content_view: 'content_view_name2'
- content_view: 'content_view_name3'
- etc.
```

Both formats are, in my humble opinion, sub par.

*Typically*, when there is a need to identify a list element by name, the attribute `name` is used - not something that describes the type of object that is defined. Especially, considering
that another role of the same collections ([`redhat.satellite.content_views`](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/content/role/content_views/)
or [`theforeman.foreman.content_views`](https://github.com/theforeman/foreman-ansible-modules/tree/develop/roles/content_views) is *requiring* the `name` attribute.

Don't get me wrong, I am not saying that it is *absolutely uncommon* to not have the `name` attribute defined, but I'd argue that this is somewhat of a common practice to use `name` over
anything else when it comes to identifying objects by *name*.

The 'list of strings format' (`legacy_a`) is even more constrained, as you can only provide a list of Content Views/Composite Content Views you'd like publish. Nothing more, no other attributes
are - of course - possible. I understand why this might seem like an easy way to get started with the role, but honestly, is it much more complicated/cumbersome to simply prepend a `name: `
in front of each Content View/Composite Content View? I don't think so :slightly_smiling_face:.

### The 'correct' format to use

Essentially, you specify your Content Views/Composite Content Views like this:

```
satellite_content_views:
- name: 'content_view_name1'
- name: 'content_view_name2'
- name: 'content_view_name3'
- etc.
```

This has two benefits:
- You can use the very same definition of Content Views/Composite Content Views as for the role ([`redhat.satellite.content_views`](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/content/role/content_views/)
- You avoid the conversion of this role which 


Role Variables
--------------
| variable                                                     | default                | required | description                                                                        |
| :----------------------------------------------------------- | :--------------------- | :------- | :--------------------------------------------------------------------------------- |
| `satellite_username`                                         | unset                  | true     | Username to authenticate with against the Satellite API                            |
| `satellite_password`                                         | unset                  | true     | Password of the user to authenticate with against the Satellite API                |
| `satellite_server_url`                                       | unset                  | true     | URL to the Satellite API (including http/s://)                                     |
| `satellite_organization`                                     | unset                  | true     | Name of the Satellite Organization to perform actions within                       |
| `satellite_content_views`                                    | unset                  | true     | Content Views and Composite Content Views to publish and optionally promote        |
| `satellite_validate_certs`                                   | `true`                 | false    | Whether to validate certificates when connecting to the Satellite API              |
| `sat_api_timestamp_format`                                   | `%Y-%m-%d %H:%M:%S %Z` | false    | Format in which the timestamps are represented in the Satellite API                |
| `sat_async_max_time`                                         | `3600`                 | false    | Time in seconds each async task runs until it times out                            |
| `sat_async_poll_time`                                        | `0`                    | false    | Poll time of each async task. Set to `0` for concurrent publish/promote actions    |
| `sat_async_retries`                                          | `1200`                 | false    | How often a async task should be checked until it is determined `failed`           |
| `sat_async_check_delay`                                      | `3`                    | false    | Delay between each check whether an async task finished                            |
| `sat_quiet_assert`                                           | `true`                 | false    | Whether to quiet assert statements                                                 |
| `sat_check_content_views_known`                              | `true`                 | false    | Check if all CVs/CCVs defined via `satellite_content_views` are known to Satellite |
| `sat_check_synchronizing_repositories`                       | `false`                | false    | Whether to check for currently synchronizing Repositories [^check_repositories]    | 
| `sat_check_successful_repository_synchronization`            | `false`                | false    | Whether to check if the last synchronization of the Repositories was successful    |
| `sat_check_unsynchronized_repositories`                      | `false`                | false    | Whether to check for unsynchronized Repositories [^check_repositories]             | 
| `sat_composite_content_view_version_description`             | `Patch day YYYY-mm-dd` | false    | Same as above, but for Composite Content View versions.                            |
| `sat_composite_content_views_allowed_lifecycle_environments` | unset                  | false    | Limit the Lifecycle Environments to which a promote *can* happen. For CCVs.        |
| `sat_content_view_version_description`                       | `Patch day YYYY-mm-dd` | false    | Description of the Content View version. Not the description of the CV itself.     |
| `sat_content_view_kinds`                                     | `both`                 | false    | Which Content View kinds to process [^content_view_kinds]                          |
| `sat_content_views_allowed_lifecycle_environments`           | unset                  | false    | Limit the Lifecycle Environments to which a promote *can* happen. For CVs.         |
| `sat_excluded_composite_content_views`                       | unset                  | false    | Exclude Composite Content Views from any activity                                  |
| `sat_excluded_content_views`                                 | unset                  | false    | Exclude Content Views from any activity                                            |
| `sat_excluded_repositories`                                  | unset                  | false    | Exclude Repositories from any activity/checks                                      |
| `sat_wait_for_repository_synchronization`                    | `false`                | false    | Whether to wait for Repositories to finish synchronizing                           | 
| `sat_publish_based_on_repository`                            | unset                  | false    | Whether to publish Content Views based on Repository synchronization date          |
| `sat_publish_based_on_component`                             | unset                  | false    | Whether to publish Composite Content Views based on their included Components      |
| `sat_show_summary`                                           | `true`                 | false    | Whether to show a summary at the end of the role, which lists all changed objects  |
| `sat_skip_legacy_conversion`                                 | `false`                | false    | Whether to skip the on-the-fly conversion of 'legacy' CV/CCV definitions           |
| `sat_skip_legacy_assert`                                     | `false`                | false    | Disable check if a legacy format can be converted                                  |
| `sat_skip_assert`                                            | `false`                | false    | Whether to skip the assert statements which check all variables (`assert.yml`)     |
| `sat_synchronize_repositories`                               | `false`                | false    | Whether to synchronize Repositories prior to publishing                            |
| `sat_convert_yaml_file`                                      | unset                  | false    | File in which the converted YAML definition will be written to (if requested)      |
| `sat_convert_yaml_indent`                                    | `2`                    | false    | What indentation (number of spaces) the converted YAML should have                 |
| `sat_convert_yaml_sort_keys`                                 | `false`                | false    | Whether to lexicographically sort keys while exporting the YAML                    |
| `sat_convert_yaml_explicit_start`                            | `true`                 | false    | Whether to add an explicit YAML beginning tag (`---`) to the converted file        |
| `sat_convert_yaml_explicit_end`                              | `true`                 | false    | Whether to add an explicit YAML ending tag (`...`) to the converted file           |
| `sat_convert_yaml_use_custom_yaml_filter`                    | `true`                 | false    | Whether to use the custom YAML filter packaged with this role                      |
| `sat_convert_yaml_top_key`                                   | `name`                 | false    | Whether to put a specific key and value to the top of a dict representing a CV/CCV |

[^check_repositories]: All Repository checks will only be performed on Repositories which are included in any Content View (and Composite Content View, technically) and are not specifically
                       excluded via `sat_excluded_repositories`.

[^content_view_kinds]: This variable can either have the value `content_views` to process only Content Views, `composite_content_views` to process only Composite Content Views or `both`
                       to process either of them. This way you can limit the activities to either Content Views or Composite Content Views, should you need to do so.

## Notes

- `sat_publish_based_on_repository` does only make sense for Content Views. Therefore, it will be skipped for Composite Content Views.
- `sat_publish_based_on_component` is only relevant for Composite Content Views, as Composite Content Views consist of one or more Components (=Content View version)

Dependencies
------------

This role makes use of the Red Hat certified collection [`redhat.satellite`](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/docs/), which is specified
via `collections/requirements.yml`.

Example Playbook
----------------

Please note, below example also contains Repositories and Components.
This is *not* required and *not* used by this role. Including these just show cases that you can use the same Content View/Composite Content View definition for this role that you'll use for
`redhat.satellite.content_views`.

### Complex example
```
---
- hosts: 'localhost'
  gather_facts: false
  roles:
    - name: 'satellite_content_view_publish_promote'
  vars:
    sat_async_max_time: 3900
    sat_async_poll_time: 0
    sat_async_retries: 2000
    sat_async_check_delay: 2
    sat_content_view_version_description: 'Patch day'
    sat_composite_content_view_version_description: 'Patch day'
    satellite_server_url: 'https://satellite.example.com'
    satellite_organization: 'org-example'
    sat_only_promote_content_views: false
    sat_only_promote_composite_content_views: false
    sat_publish_based_on_repository: true
    sat_check_unsynchronized_repositories: true
    sat_wait_for_repository_synchronization: true
    sat_check_successful_repository_synchronization: true
    sat_check_synchronizing_repositories: true
    sat_content_view_kinds: 'both'
    sat_synchronize_repositories: false
    sat_check_content_views_known: true
    sat_publish_based_on_component: true
    satellite_content_views:
      - name: 'cv-rhcdn-base-rhel-8'
        lifecycle_environments:
          - 'lce-default-dev'
          - 'lce-default-prod'

        repositories:
          - name: 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8'
            product: 'Red Hat Enterprise Linux for x86_64'

          - name: 'Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8'
            product: 'Red Hat Enterprise Linux for x86_64'

          - name: 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS Kickstart 8.9'
            product: 'Red Hat Enterprise Linux for x86_64'

          - name: 'Red Hat Enterprise Linux 8 for x86_64 - AppStream Kickstart 8.9'
            product: 'Red Hat Enterprise Linux for x86_64'

      - name: 'cv-rhcdn-base-rhel-9'
        lifecycle_environments:
          - 'lce-default-dev'

        repositories:
          - name: 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs 9'
            product: 'Red Hat Enterprise Linux for x86_64'

          - name: 'Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs 9'
            product: 'Red Hat Enterprise Linux for x86_64'

          - name: 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS Kickstart 9.3'
            product: 'Red Hat Enterprise Linux for x86_64'

          - name: 'Red Hat Enterprise Linux 9 for x86_64 - AppStream Kickstart 9.3'
            product: 'Red Hat Enterprise Linux for x86_64'

      - name: 'cv-rhcdn-satellite_6_client-rhel-8'
        patch_day_exclude: true
        repositories:
          - name: 'Red Hat Satellite Client 6 for RHEL 8 x86_64 RPMs'
            product: 'Red Hat Enterprise Linux for x86_64'

      - name: 'cv-rhcdn-satellite_6_client-rhel-9'
        patch_day_exclude: true
        repositories:
          - name: 'Red Hat Satellite Client 6 for RHEL 9 x86_64 RPMs'
            product: 'Red Hat Enterprise Linux for x86_64'

      - name: 'ccv-default-rhel-8'                                                                                                                                               
        lifecycle_environments:
          - 'lce-default-dev'
          - 'lce-default-prod'

        components:
          - content_view: 'cv-rhcdn-base-rhel-8'
            latest: true

          - content_view: 'cv-rhcdn-satellite_6_client-rhel-8'
            latest: true

      - name: 'ccv-default-rhel-9'
        lifecycle_environments:
          - 'lce-default-dev'

        components:
          - content_view: 'cv-rhcdn-base-rhel-9'
            latest: true

          - content_view: 'cv-rhcdn-satellite_6_client-rhel-9'
            latest: true
```

License
-------

GPL-2.0-or-later
