
# Default.sublime-package (upstream mirror)

I use this repository for versioning some files of the Sublime Text default packages
`Default.sublime-package` over git using two repositories strategy:

1. The first repository is mirror of some files I need to change from the latest Sublime Text
   development build version I am using. Every time a new development version is released, and I
   install it, I would unpack it, replace the files on this repository with them and commit its
   changes to this repository. This is a repository just for mirroring them. Would never be send
   changes back to this upstream from a fork repository as at every new release of Sublime Text,
   this mirror (upstream) files would be replaced and any changes would be lost lost.

1. The second repository would be a fork of this upstream mirror, on it would be included changes to
   the files at upstream mirror of Sublime Text default packages `Default.sublime-package`. Every
   Sublime Text development release would be merged the changes from the upstream mirror, if any.
   Therefore we can keep our changes while staying up-to-date with the latest version of
   `Default.sublime-package`.


Related topics about Sublime Text Default Packages:

1. [CoreIssues$621](https://github.com/SublimeTextIssues/Core/issues/621) Looking for a strategy to Open Source the "Default Packages"
1. [SublimeForum$4648](https://forum.sublimetext.com/t/request-move-all-default-packages-into-source-control/4648) REQUEST: Move all Default Packages into Source Control
1. [SublimeForum$15254](https://forum.sublimetext.com/t/packages-are-on-github/15254) Packages are on GitHub
1. [SublimeForum$22111](https://forum.sublimetext.com/t/reuse-code-of-the-default-packages/22111) Reuse code of the Default packages
1. [SublimeForum$14278](https://forum.sublimetext.com/t/looking-for-a-strategy-to-open-source-the-default-packages/14278) ★ Looking for a strategy to Open-Source the Default Packages



# License

All the files on this repository are Copyrighted for Jon Skinner @ SUBLIME HQ PTY LTD, and were
downloaded from https://www.sublimetext.com/3dev and with the following
https://www.sublimetext.com/eula `End User License Agreement`:

The SOFTWARE PRODUCT (SUBLIME TEXT) is protected by copyright laws and international copyright
treaties, as well as other intellectual property laws and treaties. The SOFTWARE PRODUCT is
licensed, not sold.

1. LICENSES

    SUBLIME TEXT is licensed as follows:

    1. Installation and Usage.

        Licenses are per user and valid for use on all supported operating systems. License keys may
        be used on multiple computers and operating systems, provided the license key holder is the
        primary user. Businesses must purchase at least as many licenses as the number of people
        using SUBLIME TEXT.

    1. Backup Copies.

        You may make copies of the license key and or SUBLIME TEXT for backup and archival purposes.

1. DESCRIPTION OF OTHER RIGHTS AND LIMITATIONS

    1. Maintenance of Copyright Notices.

        You must not remove or alter any copyright notices on any copy of SUBLIME TEXT.

    1. Distribution.

        You may not distribute or sell license keys or SUBLIME TEXT to third parties. Licenses will
        be revoked if distributed or sold to third parties.

    1. Rental.

        You may not rent, lease, or lend the license key or SUBLIME TEXT.

1. COPYRIGHT

    All title, including but not limited to copyrights, in and to SUBLIME TEXT and any copies
    thereof are owned by SUBLIME HQ PTY LTD.

1. NO WARRANTIES

    SUBLIME HQ PTY LTD expressly disclaims any warranty for SUBLIME TEXT, which is provided 'as is'
    without any express or implied warranty of any kind, including but not limited to any warranties
    of merchantability, non-infringement, or fitness of a particular purpose.

1. LIMITATION OF LIABILITY

    In no event shall SUBLIME HQ PTY LTD be liable for any damages due to use of SUBLIME TEXT, to
    the maximum extent permitted by law. This includes without limitation, lost profits, business
    interruption, or lost information. In no event will SUBLIME HQ PTY LTD be liable for loss of
    data or for indirect, special, incidental, consequential (including lost profit), or other
    damages. SUBLIME HQ PTY LTD shall have no liability with respect to the content of SUBLIME TEXT
    or any part thereof, including but not limited to errors or omissions contained therein, libel,
    trademark rights, business interruption, loss of privacy or the disclosure of confidential
    information.



