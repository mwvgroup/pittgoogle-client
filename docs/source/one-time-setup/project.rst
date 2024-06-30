.. _projects:

Google Cloud Projects
======================

.. contents::
    :depth: 2
    :local:

You will need to be authenticated to a Google Cloud project in order to access data served by Pitt-Google Broker.
Projects are free.
They are easy to create and delete.
One user can have many projects, and users can share projects.
Access is usually managed through the Google Console using a Gmail account, as shown below.

If you already have access to a Google Cloud project, you can skip this step.

.. _setup project:

Setup a Google Cloud project
--------------------------------

**Create a project**

-   Go to the
    `Cloud Resource Manager <https://console.cloud.google.com/cloud-resource-manager>`__
    and login with a Google or Gmail account (go
    `here <https://accounts.google.com/signup>`__ if you need to create one).

-   Click "Create Project" (A, in the screenshot below).

-   Enter a project name.

-   Write down the project ID (B).
    You will need it in a future step, :ref:`set env vars`.
    (You can also :ref:`find-project-id` again later.)

-   Click "Create".

.. figure:: project-setup.png
   :alt: Google Cloud project setup

.. _delete-project:

Cleanup: Delete a project
-------------------------------

If/when you are done with a Google Cloud project you can permanently delete it.
Go to the
`Cloud Resource Manager <https://console.cloud.google.com/cloud-resource-manager>`__,
select your project, and click "DELETE".
